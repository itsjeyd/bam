#!/usr/bin/env python

import os
import re
import readline
import shelve
import subprocess
import sys


RESERVED_KEYWORDS = set(
    ['help', 'setup', 'new', 'list', 'delete', 'destroy']
    )


def find_home():
    return os.path.dirname(os.path.realpath(__file__))

def handle_input(args):
    """ Entry point """
    if len(args) == 1:
        command = raw_input('yes?\n')
        if command in RESERVED_KEYWORDS:
            getattr(Bam, command)()
        else:
            Bam.run(command.split())
    elif len(args) == 2:
        command = args[1]
        if command in RESERVED_KEYWORDS:
            getattr(Bam, command)()
        else:
            Bam.run(command)
    else:
        Bam.run(args[1:])


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
        full_command = self.__replace_wildcards(input, arg_positions)
        print 'Running "%s" ... \n' % full_command
        subprocess.call(full_command, shell=True)

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
        return [alias for alias in self.database['aliases'].keys()]

    def get_commands(self):
        return [command for command in self.database['aliases'].values()]

    def get_entries(self):
        return self.database['aliases'].items()

    def add_alias(self, alias, command):
        self.database['aliases'][Alias(alias)] = Command(command)

    def rm_alias(self, alias):
        l = filter(lambda x: x == alias, self.get_aliases())
        del self.database['aliases'][l[0]]


class Bam(object):

    command_store = CommandStore()

    def db_access(func):
        def wrapper(cls, *args, **kwargs):
            Bam.command_store.access()
            if (Bam.command_store.initialized() or
                func.__name__ == 'help' or
                func.__name__ == 'setup'):
                func(cls, *args, **kwargs)
            else:
                Bam.__respond_with(
                    'Database not initialized. Please run setup first.'
                    )
            Bam.command_store.close()
        return wrapper

    @classmethod
    def __prompt_user_for(cls, string):
        return raw_input('Enter %s: ' % string)

    @classmethod
    def __respond_with(cls, string):
        print ('BAM! %s' % string)

    @classmethod
    def help(cls):
        print 'Hi! Besides "help", I respond to the following commands:'
        print '- setup'
        print '- new'
        print '- list'
        print '- delete'
        print '- destroy'

    @classmethod
    @db_access
    def setup(cls):
        try:
            Bam.command_store.init()
            Bam.__respond_with('Initialized your database.')
        except DatabaseAlreadyInitializedError:
            Bam.__respond_with(
                'No need to do that. Everything is already configured.'
                )

    @classmethod
    @db_access
    def new(cls):
        global RESERVED_KEYWORDS
        command = Bam.__prompt_user_for('command')
        if command not in Bam.command_store.get_commands():
            Bam.__respond_with('This is a brand new command.')
        else:
            Bam.__respond_with('Adding new alias to existing command...')
        alias = Bam.__prompt_user_for('alias')
        if alias in Bam.command_store.get_aliases():
            Bam.__respond_with('Can\'t do this. Alias exists.')
            return
        elif alias in RESERVED_KEYWORDS:
            Bam.__respond_with(
                'Can\'t do this. "%s" is a reserved keyword.' % alias
                )
            return
        Bam.command_store.add_alias(alias, command)
        Bam.__respond_with(
            '"%s" can now be run via "%s".' % (command, alias)
            )

    @classmethod
    @db_access
    def list(cls):
        if Bam.command_store.is_empty():
            Bam.__respond_with('You don\'t have any commands yet.')
            return
        col_width = max(map(
            lambda command: len(command), Bam.command_store.get_commands()
            )) + 2
        template = "{0:<4}{1:%d}{2}" % col_width
        print template.format('ID', "COMMAND", "ALIAS")
        for id, entry in enumerate(Bam.command_store.get_entries()):
            command = entry[1]
            alias = entry[0]
            item = (id, command, alias)
            print template.format(*item)
        print

    @classmethod
    @db_access
    def delete(cls):
        alias = Bam.__prompt_user_for('alias')
        if alias in RESERVED_KEYWORDS:
            Bam.__respond_with(
                'Can\'t do that: "%s" is a built-in command.' % alias
                )
            return
        elif alias not in Bam.command_store.get_aliases():
            Bam.__respond_with('Can\'t do that: Alias doesn\'t exist.')
            return
        print 'Srsly?'
        confirmation = Bam.__prompt_user_for('y/n')
        if confirmation == 'y':
            Bam.command_store.rm_alias(alias)
            Bam.__respond_with('"%s" is an ex-alias.' % alias)
        else:
            Bam.__respond_with('Aborting.')

    @classmethod
    def destroy(cls):
        db_path = os.path.join(find_home(), 'commands.db')
        if os.path.exists(db_path):
            print 'Really delete *everything*? This is irreversible.'
            confirmation = Bam.__prompt_user_for('y/n')
            if confirmation == 'y':
                os.remove(db_path)
                Bam.__respond_with('Nuked your database.')
            else:
                Bam.__respond_with('Aborting.')
        else:
            Bam.__respond_with('Can\'t do that. Database does not exist.')

    @classmethod
    @db_access
    def run(cls, input):
        for alias, command in Bam.command_store.get_entries():
            if alias.normalized == Input.normalized(
                input, alias.arg_positions
                ):
                command.execute(input, alias.arg_positions)
                return
        Bam.__respond_with('Unknown alias.')


class AliasCompleter(object):
    """
    """
    _options = list(RESERVED_KEYWORDS)

    def __init__(self):
        command_store = CommandStore()
        command_store.access()
        if command_store.initialized():
            self._options += command_store.get_aliases()
        command_store.close()

    def complete(self, text, state):
        if state == 0:
            if text:
                self.matches = [
                    s for s in self._options if s and s.startswith(text)
                    ]
            else:
                self.matches = self._options[:]
        try:
            return self.matches[state]
        except IndexError:
            return None

readline.set_completer(AliasCompleter().complete)
readline.parse_and_bind('tab: complete')


if __name__ == '__main__':
    handle_input(sys.argv)
