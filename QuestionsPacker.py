#!/usr/bin/env python

import argparse
import json
import os


def add_command(filename):
    # TODO write add command
    print('Add pack in ', filename)


def remove_command(question_id):
    # TODO write remove command
    print('Remove id - ', id, type(id))


def bake_command():
    bake_dir_pth = 'bake_dir'
    result_filename = 'questions_list.json'

    whole_pack = list()
    last_id = 0
    for dirname in os.listdir(bake_dir_pth):
        if dirname == '.gitkeep':
            continue
        filename = '{}/{}'.format(bake_dir_pth, dirname)
        kek = open(filename, 'r', encoding='utf-8').read()
        pack = json.loads(kek)
        for elem in pack:
            elem['id'] = last_id
            last_id += 1
            whole_pack.append(elem)
        print('Baked {}'.format(filename))
    open(result_filename, 'w', encoding='utf-8').write(json.dumps(whole_pack, ensure_ascii=False))
    print('Baked {} elements'.format(last_id))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', type=str, default='')
    parser.add_argument('--remove', type=int, default=-1)
    parser.add_argument('--bake', action='store_true')
    args = parser.parse_args()

    if args.bake:
        bake_command()
    elif args.add:
        add_command(args.add)
    elif args.remove != -1:
        remove_command(args.remove)
    else:
        print('Unknown command')


if __name__ == "__main__":
    main()
