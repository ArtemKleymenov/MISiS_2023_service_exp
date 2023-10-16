from abc import ABC, abstractmethod
import threading
import socket
from typing import Optional, Callable


class Service(ABC):
#private:
    def __init__(self, ip_: str, port_: int, request_handler_: Callable[[str], str], n_conn_=10, bytes_=1024):
        self.ip      = ip_
        self.port    = port_
        self.n_conn  = n_conn_
        self.bytes   = bytes_
        self.sleep   = 10
        self.timeout = 3

        self.request_handler  = request_handler_

        self.need_job_break = False
        self.need_job_pause = True
        self.server_is_open = True
        self.need_restart   = False

        self.server            = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_clients = []
        

    def __manage_clients(self) -> None:
        service_closing_commands = []
        while True:
            if len(self.connected_clients) == 0 and not self.server_is_open:
                break
            if len(self.connected_clients) == 0:
                continue
            while len(self.connected_clients) > 0:
                client_socket = self.connected_clients[0]
                self.connected_clients.pop(0)

                try:
                    request = client_socket.recv(self.bytes)
                    request = request.decode("utf-8")
                    print(f"Received: {request}")

                    if request.lower() == "disable":
                        self.pause()
                        client_socket.send("disable success".encode("utf-8"))
                    elif request.lower() == "enable":
                        self.unpause()
                        client_socket.send("enable success".encode("utf-8"))
                    elif request.lower() == "close" or request.lower() == "restart":
                        self.stop()
                        service_closing_commands.append(request.lower())
                        client_socket.send(("beginning " + request.lower()).encode("utf-8"))
                    else:
                        result = self.request_handler(request)
                        client_socket.send(result.encode("utf-8"))
                except Exception as e:
                    print(f"Server error when handling client: {e}")
                finally:
                    client_socket.close()
        if len(service_closing_commands) > 0:
            if service_closing_commands[0] == "restart":
                self.need_restart = True

#protected:
    @abstractmethod
    def _do_job(self):
        pass

    def _run_client(self, ip: str, port: int, request: str, response_handler: Optional[Callable[[str], None]] = None) -> None:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))

            client.send(request.encode("utf-8")[:self.bytes])
            response = client.recv(self.bytes)
            response = response.decode("utf-8")
            print(f"Received: {response}")

            if response_handler is not None:
                response_handler(response)
        except Exception as e:
            print(f"Client error when handling client: {e}")
        finally:
            client.close()
            print("Connection to server closed")

#public:
    def run_client(self, ip: str, port: int, request: str, response_handler: Optional[Callable] = None) -> None:
        client_thread = threading.Thread(target=self._run_client, args=(ip, port, request, response_handler,))
        client_thread.start()

    def start(self) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(self.timeout)
        self.server.bind((self.ip, self.port))
        self.server.listen(self.n_conn)
        print(f"Listening on {self.ip}:{self.port}")

        job_thread = threading.Thread(target=self.__manage_clients, args=())
        job_thread.start()

        client_managing_thread = threading.Thread(target=self._do_job, args=())
        client_managing_thread.start()

        while self.server_is_open:
            try:
                client_socket, client_address = self.server.accept()
                self.connected_clients.append(client_socket)
                print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            except socket.timeout:
                pass
        client_managing_thread.join()
        self.server.close()

        if self.need_restart:
            self.restart()

    def stop(self) -> None:
        self.server_is_open = False
        self.need_job_break = True

    def pause(self) -> None:
        self.need_job_pause = False

    def unpause(self) -> None:
        self.need_job_pause = True

    def restart(self) -> None:
        self.need_job_break    = False
        self.need_job_pause    = True
        self.server_is_open    = True
        self.need_restart      = False
        self.connected_clients = []
        self.start()
