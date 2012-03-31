#!/usr/bin/env python

import os
import re
import shelve
import subprocess
import sys


def read_path():
    with open('path') as pathfile:
        return pathfile.next()

def handle_input(args):
    """ Entry point """
    if len(sys.argv) == 1:
        pass
    elif len(sys.argv) == 2:
        pass
    else:
        pass


class Bam:

    @classmethod
    def setup(cls):
        if not os.path.exists('path'):
            with open('path', 'w') as pathfile:
                pathfile.write(os.getcwd())
            COMMAND_STORE = shelve.open(
                os.path.join(os.getcwd(), 'commands.db'), writeback=True
                )
            COMMAND_STORE['aliases'] = dict()
            COMMAND_STORE.close()
            print 'BAM! Done configuring. Time to add some aliases!'
        else:
            print 'BAM! No need to do that. Everything is already configured.'

    @classmethod
    def new(cls):
        command = raw_input('Enter command: ')
        if command not in COMMAND_STORE['aliases'].values():
            print 'BAM! This is a brand new command.'
        arguments = dict()

        alias = raw_input('Enter alias: ')
        if '[' or ']' in alias:
            words = re.sub('[\[\]]', '', alias).split()
            for word in words:
                if re.match('\d+', word):
                    arguments[word] = words.index(word)

        COMMAND_STORE['aliases'][alias] = (command, arguments)
        print 'BAM! %s can now be run via %s.' % (command, alias)

    @classmethod
    def show(cls):
        try:
            col_width = max(map(
                lambda x: len(x),
                [c[0] for c in COMMAND_STORE['aliases'].values()]
                )) + 2
            template = "{0:<4}{1:%d}{2}" % col_width
            print template.format('ID', "COMMAND", "ALIAS")
            for id, entry in enumerate(COMMAND_STORE['aliases'].items()):
                command = entry[1][0]
                alias = entry[0]
                item = (id, command, alias)
                print template.format(*item)
            print
        except ValueError:
            print 'You don\'t have any commands yet.'
        except KeyError:
            print 'You need to initialize your database.'

    @classmethod
    def delete(cls):
        confirmation = raw_input('Really Papi? ')
        if confirmation == 'really':
            alias = ' '.join(sys.argv[2:])
            try:
                del COMMAND_STORE['aliases'][alias]
                print 'BAM! %s is an ex-alias.' % alias
            except KeyError:
                print 'BAM! Can\'t do that: Alias doesn\'t exist.'
        else:
            print 'Deleting an alias is serious business!\n' \
                  'I won\'t do it unless you\'re absolutely sure.'

    @classmethod
    def destroy(cls):
        COMMAND_STORE.close()
        os.remove(os.path.join(read_path(), 'commands.db'))
        os.remove(os.path.join(read_path(), 'path'))
        print 'BAM! Nuked your database and config.'

    @classmethod
    def run(cls):
        # TODO Wildcard handling
        input = sys.argv[1:]
        for alias, entry in COMMAND_STORE['aliases'].items():
            norm_alias = ' '.join(
                word for word in alias.split() if not
                ('[' in word or ']' in word)
                )
            args = entry[1].values()
            norm_input = ' '.join(
                word for word in input if not input.index(word) in args
                )
            if norm_alias == norm_input:
                command = entry[0].split()
                for key, value in entry[1].items():
                    pos = entry[0].split().index('[%s]' % key)
                    command[pos] = input[entry[1][key]]
                command = ' '.join(command)
                try:
                    subprocess.call(command, shell=True)
                    print command
                except KeyError:
                    print 'You don\'t have any commands associated with this alias'


if __name__ == '__main__':
    if sys.argv[1] == 'setup':
       Bam.setup()
    else:
        try:
            COMMAND_STORE = shelve.open(
                os.path.join(read_path(), 'commands.db'), writeback=True
                )
            if sys.argv[1] == 'new':
                Bam.new()
            elif sys.argv[1] == 'list' and len(sys.argv) == 2:
                Bam.show()
            elif sys.argv[1] == 'del':
                Bam.delete()
            elif sys.argv[1] == 'destroy':
                Bam.destroy()
            else:
                Bam.run()
        except IOError:
            print 'BAM! Can\'t access database. Please run setup first.'
