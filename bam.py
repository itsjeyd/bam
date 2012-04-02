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


class Alias(object):
    """
    """

    def __init__(self, string):
        self._string = string
        self._tokens = string.split()

    def __repr__(self):
        return self._string

    @property
    def arg_positions(self):
        args = dict()
        if '[' or ']' in self._string:
            words = re.sub('[\[\]]', '', self._string).split()
            for word in words:
                if re.match('\d+', word):
                    args[word] = words.index(word)
        return args

    @property
    def normalized(self):
        return ' '.join(
            token for token in self._tokens if not
            self._tokens.index(token) in self.arg_positions.values()
            )


class Command(Alias):
    """
    """

    def execute(self, input, arg_positions):
        subprocess.call(
            self.__replace_wildcards(input, arg_positions), shell=True
            )

    def __replace_wildcards(self, input, arg_positions):
        full_command = self._tokens
        for arg, pos in arg_positions.items():
            full_command[self.arg_positions[arg]] = input.split()[pos]
        return ' '.join(full_command)


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

    def is_empty(self):
        return True if not self.database.items() else False

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
        if cls.COMMAND_STORE.is_empty():
            print 'BAM! You don\'t have any commands yet.'
            return
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

    @classmethod
    @db_access
    def delete(cls):
        alias = cls.__prompt_user_for('alias')
        if alias not in cls.COMMAND_STORE.get_aliases():
            print 'BAM! Can\'t do that: Alias doesn\'t exist.'
            return
        print 'Srsly?'
        confirmation = cls.__prompt_user_for('y/n')
        if confirmation == 'y':
            cls.COMMAND_STORE.rm_alias(alias)
            print 'BAM! "%s" is an ex-alias.' % alias
        else:
            print 'BAM! Aborting.'

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
            arg_positions = entry[1].values()
            norm_alias = cls.__remove_arg_positions(
                alias.split(), arg_positions
                )
            norm_input = cls.__remove_arg_positions(input, arg_positions)
            if norm_alias == norm_input:
                command = entry[0].split()
                for arg, inputpos in entry[1].items():
                    pos = command.index('[%s]' % arg)
                    command[pos] = input[inputpos]
                command = ' '.join(command)
                print 'Running "%s" ...' % command
                subprocess.call(command, shell=True)
                return
        print 'BAM! Unknown alias.'

    @classmethod
    def __remove_arg_positions(cls, words, arg_positions):
        return ' '.join(
            word for word in words if not words.index(word) in arg_positions
            )


if __name__ == '__main__':
    handle_input(sys.argv)
