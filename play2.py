from re import compile, finditer

IMG_REGEX = compile(r'IMAGE\(([^)]+)\)')


def main():
    s = 'Hello world IMAGE(jaribio.png) now isn\'t that great? IMAGE(seif.png)'
    s2 = 'blah blah'
    process(s)
    process(s2)


def process(s):
    start_ind = 0
    for match in finditer(IMG_REGEX, s):
        match_start, match_end = match.span()
        print(s[start_ind: match_start]).split()
        print('using pic {} '.format(match.group(1)))
        start_ind = match_end
    print(s[start_ind:])


if __name__ == '__main__':
    main()
