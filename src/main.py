from data_import.import_y import import_y


def main():
    y = import_y("data/raw/y.csv")
    print(y.head())


if __name__ == "__main__":
    main()
