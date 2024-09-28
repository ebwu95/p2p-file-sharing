import os
import hashlib

CHUNK_SIZE = 512 #Moto moto

def chunk_file(file):
    chunks = []
    with open(file, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks

def save_chunks(chunks, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(output_dir, f'chunk_{i:04d}')
        with open(chunk_path, 'wb') as f:
            f.write(chunk)

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def reassemble_file(chunks, output_file, original_hash):
    with open(output_file, 'wb') as f:
        for chunk in chunks:
            f.write(chunk)
    
    reassembled_hash = compute_sha256(output_file)
    if reassembled_hash != original_hash:
        raise ValueError("Hash status: mismatch\nThe file may be corrupted :(")
    else:
        print("Hash status: match\nMoto moto says good job")