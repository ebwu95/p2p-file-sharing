import os

def chunk_file(file_path, chunk_size=512):
    chunks = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
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

def main():
    file_path = input("Enter the path of the file to chunk: ")
    output_dir = input("Enter the directory to save chunks: ")
    
    chunks = chunk_file(file_path)
    save_chunks(chunks, output_dir)
    print(f"File chunked into {len(chunks)} chunks and saved in {output_dir}")

if __name__ == "__main__":
    main()