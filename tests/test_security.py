import unittest
import os
from app.security import encrypt_password, decrypt_password, KEY_FILE

class TestSecurity(unittest.TestCase):
    def test_plaintext_fallback(self):
        # Senhas sem prefixo 'enc:' devem retornar intactas
        self.assertEqual(decrypt_password("minhasenha123"), "minhasenha123")
        self.assertEqual(decrypt_password(""), "")
        self.assertIsNone(decrypt_password(None))

    def test_encryption_decryption_flow(self):
        original = "MinhaSenhaSuperSecreta@2026!"
        encrypted = encrypt_password(original)
        
        # O resultado criptografado deve começar com 'enc:'
        self.assertTrue(encrypted.startswith("enc:"))
        self.assertNotEqual(encrypted, original)
        
        # Descriptografia deve recuperar o valor original
        decrypted = decrypt_password(encrypted)
        self.assertEqual(decrypted, original)

    def test_corrupt_encrypted_string(self):
        # String com prefixo 'enc:' inválida deve retornar a si mesma (ou não estourar erro fatal)
        corrupted = "enc:string_invalida_totalmente_corrompida"
        decrypted = decrypt_password(corrupted)
        # Retorna o valor original para evitar que o app trave
        self.assertEqual(decrypted, corrupted)

if __name__ == "__main__":
    unittest.main()
