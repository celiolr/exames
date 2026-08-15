import os
import sys
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def get_encryption_key():
    """
    Obtém ou gera a chave de criptografia.
    Tenta ler da variável de ambiente EXAMES_ENCRYPTION_KEY primeiro,
    depois do arquivo 'secret.key' no diretório raiz.
    Se não existir, gera uma chave nova e salva em 'secret.key'.
    """
    # 1. Tentar variável de ambiente
    key_env = os.environ.get("EXAMES_ENCRYPTION_KEY")
    if key_env:
        try:
            # Validar se a chave é válida para o Fernet
            key_bytes = key_env.encode('utf-8')
            Fernet(key_bytes)
            return key_bytes
        except Exception:
            pass

    # 2. Tentar arquivo secret.key
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "rb") as f:
                key_bytes = f.read().strip()
                Fernet(key_bytes)
                return key_bytes
        except Exception:
            pass

    # 3. Gerar nova chave se não existir
    new_key = Fernet.generate_key()
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(new_key)
        # Garantir que o secret.key seja adicionado ao .gitignore se ainda não estiver
        _add_to_gitignore(KEY_FILE)
    except Exception as e:
        print(f"Erro ao salvar a chave no arquivo {KEY_FILE}: {e}", file=sys.stderr)
    
    return new_key

def _add_to_gitignore(filename):
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            if filename not in lines:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{filename}\n")
        except Exception:
            pass

def encrypt_password(password: str) -> str:
    """
    Criptografa a senha em texto plano e retorna a string criptografada
    com o prefixo 'enc:'.
    """
    if not password:
        return ""
    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted_bytes = fernet.encrypt(password.encode('utf-8'))
    return f"enc:{encrypted_bytes.decode('utf-8')}"

def decrypt_password(password_str: str) -> str:
    """
    Descriptografa a senha se ela estiver no formato 'enc:<ciphertext>'.
    Caso contrário, retorna a senha como está (compatibilidade com texto plano).
    """
    if not password_str or not password_str.startswith("enc:"):
        return password_str
    
    try:
        ciphertext = password_str[4:]
        key = get_encryption_key()
        fernet = Fernet(key)
        decrypted_bytes = fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Se falhar por qualquer motivo (chave incorreta ou corrupção), retorna a string original
        print(f"Erro ao descriptografar senha: {e}", file=sys.stderr)
        return password_str

if __name__ == "__main__":
    print("=== Utilitário de Criptografia de Senha ===")
    print(f"Chave carregada de/salva em: {KEY_FILE}\n")
    
    pwd = ""
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        import getpass
        try:
            pwd = getpass.getpass("Digite a senha que deseja criptografar (ou passe como argumento): ")
        except KeyboardInterrupt:
            print("\nOperação cancelada.")
            sys.exit(0)
            
    if not pwd:
        print("Senha vazia. Operação cancelada.")
        sys.exit(1)
        
    encrypted = encrypt_password(pwd)
    print("\nUse a string abaixo no seu config.ini:")
    print("-" * 60)
    print(encrypted)
    print("-" * 60)
