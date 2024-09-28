import unittest
import os
import shutil
from file_utils import chunk_file, save_chunks, compute_sha256, reassemble_file

class TestFileUtils(unittest.TestCase):

    def setUp(self):
        self.test_dir = 'test_chunks'
        self.reassembled_file = 'reassembled_file.txt'
        self.test_file = input("Enter the name of the text file for testing (with extension): ")
        if not os.path.exists(self.test_file):
            raise FileNotFoundError(f"The file {self.test_file} does not exist in the current directory.")

    def tearDown(self):
        if os.path.exists(self.reassembled_file):
            os.remove(self.reassembled_file)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_chunk_and_reassemble(self):
        original_hash = compute_sha256(self.test_file)
        chunks = chunk_file(self.test_file)
        save_chunks(chunks, self.test_dir)
        loaded_chunks = []
        for i in range(len(chunks)):
            chunk_path = os.path.join(self.test_dir, f'chunk_{i:04d}')
            with open(chunk_path, 'rb') as f:
                loaded_chunks.append(f.read())

        reassemble_file(loaded_chunks, self.reassembled_file, original_hash)

        reassembled_hash = compute_sha256(self.reassembled_file)
        self.assertEqual(original_hash, reassembled_hash, "Hash mismatch! The file may be corrupted :(")

if __name__ == '__main__':
    unittest.main()