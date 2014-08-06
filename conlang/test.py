from soundChanger import applyRule
cats = {'V': ['u', 'z', 'i', 'ɯ', 'a'],
        'F': ['f', 's', 'ç', 'x', 'ħ']}
rules = [{'from': '{0:F}', 'to': '{0:V}', 'before': '{F}', 'after': '{F}'},
         {'from': '{0:V}', 'to': '{0:F}', 'before': '{V}', 'after': '{V}'}]
word = input()
#word = 'ħsfuza'

print(word)

for rule in rules:
    print(rule)
    word = applyRule(word, rule, cats)
    print(word)
