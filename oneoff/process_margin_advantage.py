import collections

def analyze(name, margin_supply_tuples):
    length = len(margin_supply_tuples)
    median = length / 2 
    median_margin = margin_supply_tuples[median][0]
    first_0, last_0 = -1, -1
    for ind, (margin, supply) in enumerate(margin_supply_tuples):
        if margin == 0:
            if first_0 == -1:
                first_0 = ind
            last_0 = ind
    def perc(f):
        return 100.0 * float(f) / length
    print name, ',', median_margin, ',', perc(first_0), ',', perc(last_0)

def main():
    margin_supply_tuples = []
    for line_idx, line in enumerate(open('margin.txt', 'r')):
        try:
            split_line = line.strip().split(':')
            margin_supply_tuples.append((float(split_line[0]), 
                                         split_line[1].split(',')))
        except IndexError:
            print line
    margin_supply_tuples.sort()
    by_card = collections.defaultdict(list)
    for margin, supply in margin_supply_tuples:
        for card in supply:
            by_card[card].append((margin, supply))
    analyze('all', margin_supply_tuples)
    for card, margin_list in by_card.iteritems():
        analyze(card, margin_list)

if __name__ == '__main__':
    main()

