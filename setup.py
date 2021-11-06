def count_lines(file):
    # Adapted from https://www.kite.com/python/answers/how-to-get-a-line-count-of-a-file-in-python
    # A quick way to count the numbers of dependencies installed
    file = open(file, "r")
    nonempty_lines = [line.strip("\n") for line in file if line != "\n"]

    line_count = len(nonempty_lines)
    file.close()
	
    return line_count


def setup_dependency():
    line_count = count_lines("requirements.txt")
    print(str(line_count) + " dependencies installed...")


