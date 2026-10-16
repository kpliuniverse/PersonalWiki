import sys

from test_runs import make_wiki

if __name__ == "__main__": 
    {
        "make_wiki": make_wiki.main
    }[sys.argv[1]]()