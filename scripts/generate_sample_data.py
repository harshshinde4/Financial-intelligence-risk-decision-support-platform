from financial_ai.data.sample_data import write_sample_datasets

if __name__ == "__main__":
    paths = write_sample_datasets()
    for path in paths:
        print(path)
