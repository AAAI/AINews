from AINewsTextProcessor import *

#######################################
#
#        Test code
#
#######################################
def read_raw_document(filename):
    """
    File I/O operation to read in the file from the disk, and save into
    self.raw.
    """
    try:
        f = open(filename, 'r')
    except IOError:
        print 'cannot open', filename
    else:
        raw = f.read()
        f.close()
        return raw


def main():
    processor = AINewsTextProcessor(False)
    raw  = read_raw_document('news/text/1.txt')
    
    wordfreq = processor.simpletextprocess(raw)
    for word in wordfreq:
        print word, wordfreq[word]
    """
    unigrams = processor.unigrams(raw)
    for unigram in unigrams:
        print unigram
    """
    '''
    bigrams = processor.bigrams(unigrams)
    for bigram in bigrams:
        print bigram,
    '''

    
if __name__ == "__main__":
    main()

