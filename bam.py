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
    if len(sys.argv) == 1:
        print 'yes?'
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'setup':
            Bam.setup()
        elif sys.argv[1] == 'new':
            Bam.new()
        elif sys.argv[1] == 'list':
            Bam.show()
        elif sys.argv[1] == 'del':
            Bam.delete()
        elif sys.argv[1] == 'destroy':
            Bam.destroy()
    else:
        Bam.run()


class Input(str):
    """
    """

    @staticmethod
    def normalized(input, arg_positions):
        return ' '.join(
            token for token in input if not
            input.index(token) in arg_positions.values()
            )


class Alias(Input):
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
        return super(Alias, self).normalized(self._tokens, self.arg_positions)


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
            full_command[self.arg_positions[arg]] = input[pos]
        return ' '.join(full_command)


class DatabaseAlreadyInitializedError(StandardError):
    pass


class CommandStore(object):
    """
    """
    database = None

    def init(self):
        if not self.database.has_key('aliases'):
            self.database['aliases'] = dict()
        else:
            raise DatabaseAlreadyInitializedError

    def access(self):
        self.database = shelve.open(
            os.path.join(find_home(), 'commands.db'), writeback=True
            )

    def close(self):
        self.database.close()

    def initialized(self):
        return self.database.has_key('aliases')

    def is_empty(self):
        return True if not self.database['aliases'].items() else False

    def get_aliases(self):
        return [str(alias) for alias in self.database['aliases'].keys()]

    def get_commands(self):
        return [str(command) for command in self.database['aliases'].values()]

    def get_entries(self):
        return self.database['aliases'].items()

    def add_alias(self, alias, command):
        self.database['aliases'][Alias(alias)] = Command(command)

    def rm_alias(self, alias):
        l = filter(lambda x: str(x) == alias, self.get_aliases())
        del self.database['aliases'][l[0]]


class Bam:

    COMMAND_STORE = CommandStore()

    def db_access(func):
        def wrapper(cls, *args, **kwargs):
            Bam.COMMAND_STORE.access()
            if Bam.COMMAND_STORE.initialized() or func.__name__ == 'setup':
                func(cls, *args, **kwargs)
            else:
                Bam.__respond_with(
                    'Database not initialized. Please run setup first.'
                    )
            Bam.COMMAND_STORE.close()
        return wrapper

    @classmethod
    def __prompt_user_for(cls, string):
        return raw_input('Enter %s: ' % string)

    @classmethod
    def __respond_with(cls, string):
        print ('BAM! %s' % string)

    @classmethod
    @db_access
    def setup(cls):
        try:
            Bam.COMMAND_STORE.init()
            Bam.__respond_with('Initialized your database.')
        except DatabaseAlreadyInitializedError:
            Bam.__respond_with(
                'No need to do that. Everything is already configured.'
                )

    @classmethod
    @db_access
    def new(cls):
        command = Bam.__prompt_user_for('command')
        if command not in Bam.COMMAND_STORE.get_commands():
            Bam.__respond_with('This is a brand new command.')
        else:
            Bam.__respond_with('Adding new alias to existing command...')
        alias = Bam.__prompt_user_for('alias')
        if alias in Bam.COMMAND_STORE.get_aliases():
            Bam.__respond_with('Can\'t do this. Alias exists.')
            return
        Bam.COMMAND_STORE.add_alias(alias, command)
        Bam.__respond_with(
            '"%s" can now be run via "%s".' % (command, alias)
            )

    @classmethod
    @db_access
    def show(cls):
        if Bam.COMMAND_STORE.is_empty():
            Bam.__respond_with('You don\'t have any commands yet.')
            return
        col_width = max(map(
            lambda command: len(command), Bam.COMMAND_STORE.get_commands()
            )) + 2
        template = "{0:<4}{1:%d}{2}" % col_width
        print template.format('ID', "COMMAND", "ALIAS")
        for id, entry in enumerate(Bam.COMMAND_STORE.get_entries()):
            command = entry[1]
            alias = entry[0]
            item = (id, command, alias)
            print template.format(*item)
        print

    @classmethod
    @db_access
    def delete(cls):
        alias = Bam.__prompt_user_for('alias')
        if alias not in Bam.COMMAND_STORE.get_aliases():
            Bam.__respond_with('Can\'t do that: Alias doesn\'t exist.')
            return
        print 'Srsly?'
        confirmation = Bam.__prompt_user_for('y/n')
        if confirmation == 'y':
            Bam.COMMAND_STORE.rm_alias(alias)
            Bam.__respond_with('"%s" is an ex-alias.' % alias)
        else:
            Bam.__respond_with('Aborting.')

    @classmethod
    def destroy(cls):
        db_path = os.path.join(find_home(), 'commands.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            Bam.__respond_with('Nuked your database.')
        else:
            Bam.__respond_with('Can\'t do that. Database does not exist.')

    @classmethod
    @db_access
    def run(cls):
        input = sys.argv[1:]
        for alias, command in Bam.COMMAND_STORE.get_entries():
            if alias.normalized == Input.normalized(
                input, alias.arg_positions
                ):
                command.execute(input, alias.arg_positions)
                return
        Bam.__respond_with('Unknown alias.')


if __name__ == '__main__':
    handle_input(sys.argv)
