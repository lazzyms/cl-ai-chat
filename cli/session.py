from colorama import Fore, Style


def get_file_ids():
    print()
    print(f"{Fore.BLUE} Document Session Setup{Style.RESET_ALL}")
    print("Enter the file_id of the document you want to explore.")
    print("Hit 'enter' if you want to continue without a document. \n")

    while True:
        file_id = input(f"{Fore.CYAN}file_id: {Style.RESET_ALL}").strip()

        if not file_id:
            return None

        return file_id
