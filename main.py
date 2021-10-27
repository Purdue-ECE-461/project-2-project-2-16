import sys
from command import figure_out_command, write_log_file


if __name__ == '__main__':
    figure_out_command(sys.argv[1])

    write_log_file()
