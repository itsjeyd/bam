#!/usr/bin/env python

import os
import re
import shelve
import subprocess
import sys


def find_home():
    return os.path.dirname(os.path.realpath(__file__))

def handle_input(args):
    """ Entry point """
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

    # if len(sys.argv) == 1:
    #     pass
    # elif len(sys.argv) == 2:
    #     pass
    # else:
    #     pass


class CommandStore(object):
    """
    """
    database = None

    def access(self):
        self.database = shelve.open(
            os.path.join(find_home(), 'commands.db'), writeback=True
            )

    def close(self):
        self.database.close()

    def get_aliases(self):
        return self.database.keys()

    def get_commands(self):
        return [x[0] for x in self.database.values()]

    def get_entries(self):
        return self.database.items()

    def add_alias(self, alias, command, arguments):
        self.database[alias] = (command, arguments)

    def rm_alias(self, alias):
        del self.database[alias]


class Bam:

    COMMAND_STORE = CommandStore()

    def db_access(func):
        def wrapper(cls, *args, **kwargs):
            cls.COMMAND_STORE.access()
            func(cls, *args, **kwargs)
            cls.COMMAND_STORE.close()
        return wrapper

    @classmethod
    def __prompt_user_for(cls, string):
        return raw_input('Enter %s: ' % string)

    @classmethod
    @db_access
    def new(cls):
        command = cls.__prompt_user_for('command')
        if command not in cls.COMMAND_STORE.get_commands():
            print 'BAM! This is a brand new command.'
        else:
            print 'BAM! Adding new alias to existing command...'
        alias = cls.__prompt_user_for('alias')
        if alias in cls.COMMAND_STORE.get_aliases():
            print 'BAM! Can\'t do this. Alias exists.'
            return
        arguments = cls.__extract_args(alias)
        cls.COMMAND_STORE.add_alias(alias, command, arguments)
        print 'BAM! "%s" can now be run via "%s".' % (command, alias)

    @classmethod
    def __extract_args(cls, alias):
        args = dict()
        if '[' or ']' in alias:
            words = re.sub('[\[\]]', '', alias).split()
            for word in words:
                if re.match('\d+', word):
                    args[word] = words.index(word)
        return args

    @classmethod
    @db_access
    def show(cls):
        try:
            col_width = max(map(
                lambda command: len(command), cls.COMMAND_STORE.get_commands()
                )) + 2
            template = "{0:<4}{1:%d}{2}" % col_width
            print template.format('ID', "COMMAND", "ALIAS")
            for id, entry in enumerate(cls.COMMAND_STORE.get_entries()):
                command = entry[1][0]
                alias = entry[0]
                item = (id, command, alias)
                print template.format(*item)
            print
        except ValueError:
            print 'BAM! You don\'t have any commands yet.'

    @classmethod
    @db_access
    def delete(cls):
        confirmation = raw_input('Really Papi? ')
        if confirmation == 'really':
            alias = ' '.join(sys.argv[2:])
            try:
                cls.COMMAND_STORE.rm_alias(alias)
                print 'BAM! "%s" is an ex-alias.' % alias
            except KeyError:
                print 'BAM! Can\'t do that: Alias doesn\'t exist.'
        else:
            print 'Deleting an alias is serious business!\n' \
                  'I won\'t do it unless you\'re absolutely sure.'

    @classmethod
    def destroy(cls):
        os.remove(os.path.join(find_home(), 'commands.db'))
        print 'BAM! Nuked your database.'

    @classmethod
    @db_access
    def run(cls):
        # TODO Wildcard handling
        input = sys.argv[1:]
        for alias, entry in cls.COMMAND_STORE.get_entries():
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
                subprocess.call(command, shell=True)
                print command


if __name__ == '__main__':
    handle_input(sys.argv)
