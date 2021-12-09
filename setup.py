'''
Quick way to check how many dependencies are installed
'''

def count_lines(file):
    '''
    Adapted from https://www.kite.com/python/answers/how-to-get-a-line-count-of-a-file-in-python
    A quick way to count the numbers of dependencies installed
    '''
    with open(file, "r"):
        data = file.read()
        nonempty_lines = [line.strip("\n") for line in data if line != "\n"]
        line_count = len(nonempty_lines)

    return line_count

def setup_dependency():
    '''
    Use how many lines are in the file to infer how many dependencies are installed
    '''
    line_count = count_lines("requirements.txt")
    print(str(line_count) + " dependencies installed...")
