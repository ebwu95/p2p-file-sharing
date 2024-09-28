import os

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

def reassemble_file(chunks, output_file):
    with open(output_file, 'wb') as f:
        for chunk in chunks:
            f.write(chunk)

def save_chunks(chunks, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(output_dir, f'chunk_{i:04d}')
        with open(chunk_path, 'wb') as f:
            f.write(chunk)
