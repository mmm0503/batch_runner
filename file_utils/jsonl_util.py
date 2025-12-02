class JSONLUtil:

    @staticmethod
    def read_jsonl(file_path):
        """Read a JSONL file and return a list of dictionaries."""
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data.append(json.loads(line.strip()))
        return data

    @staticmethod
    def write_jsonl(file_path, data):
        """Write a list of dictionaries to a JSONL file."""
        with open(file_path, 'w', encoding='utf-8') as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + '\n')
