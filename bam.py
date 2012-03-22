#!/usr/bin/env python

import re
import shelve
import subprocess
import sys


#####################################################################
# ID  COMMAND                          ALIAS                        #
# 0   git push origin master           push it real good            #
# 1   cp -R * [0]                      copy all files to [0]        #
# 2   ls [0] | grep [1]                show me all [1] files in [0] #
# 3   rm *~                            get rid of temp files        #
# 4   du -sh /var/cache/apt/archives/  how big is apt cache         #
# 5   chmod +x [0]                     make [0] executable          #
# 6   bam list                         show me my aliases           #
#####################################################################


if __name__ == '__main__':
    COMMAND_STORE = shelve.open('/home/tim/bam/commands.db', writeback=True)

    if sys.argv[1] == 'create':
        if not COMMAND_STORE.has_key('aliases'):
            COMMAND_STORE['aliases'] = dict()
            print 'BAM! Initialized database commands.db.'

    elif sys.argv[1] == 'new':
        command = raw_input('Enter command: ')
        if command not in COMMAND_STORE['aliases'].values():
            print 'BAM! This is a brand new command.'
        arguments = dict()

        alias = raw_input('Enter alias: ')
        if '[' or ']' in alias:
            words = re.sub('[\[\]]', '', alias).split()
            for i in words:
                if re.match('\d+', i):
                    arguments[i] = words.index(i)

        COMMAND_STORE['aliases'][alias] = (command, arguments)
        print 'BAM! %s can now be run via %s.' % (command, alias)

    elif sys.argv[1] == 'list' and len(sys.argv) == 2:
        # TODO: Add error handling here (bam list fails if commands.db is empty)
        l = max(map(lambda x: len(x), [c[0] for c in COMMAND_STORE['aliases'].values()])) + 2
        template = "{0:<4}{1:%d}{2}" % l
        print template.format('ID', "COMMAND", "ALIAS")
        for id, entry in enumerate(COMMAND_STORE['aliases'].items()):
            command = entry[1][0]
            alias = entry[0]
            item = (id, command, alias)
            print template.format(*item)
        print

    elif sys.argv[1] == 'del':
        confirmation = raw_input('Really Papi? ')
        if confirmation == 'really':
            alias = ' '.join(sys.argv[2:])
            try:
                del COMMAND_STORE['aliases'][alias]
                print '%s is an ex-alias' % alias
            except KeyError:
                print 'I don\'t know what you\'re talking about.'

    else:
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
