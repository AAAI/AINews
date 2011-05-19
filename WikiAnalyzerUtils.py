# ====================================================================
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ====================================================================

from lucene import \
     SimpleAnalyzer, StandardAnalyzer, StringReader, Version, \
     TermAttribute, PositionIncrementAttribute, TypeAttribute, \
     OffsetAttribute


class WikiAnalyzerUtils(object):

    def main(cls, argv):

        print "SimpleAnalyzer"
        cls.displayTokensWithFullDetails(SimpleAnalyzer(),
                                         "The quick brown fox....")

        print "\n----"
        print "StandardAnalyzer"
        cls.displayTokensWithFullDetails(StandardAnalyzer(Version.LUCENE_CURRENT), "I'll e-mail you at xyz@example.com")

    def setPositionIncrement(cls, source, posIncr):
        attr = source.addAttribute(PositionIncrementAttribute.class_)
        attr.setPositionIncrement(posIncr)

    def getPositionIncrement(cls, source):
        attr = source.addAttribute(PositionIncrementAttribute.class_)
        return attr.getPositionIncrement()

    def setTerm(cls, source, term):
        attr = source.addAttribute(TermAttribute.class_)
        attr.setEmpty()
        attr.append(term)

    def getTerm(cls, source):
        attr = source.addAttribute(TermAttribute.class_)
        return attr.toString()

    def setType(cls, source, type):
        attr = source.addAttribute(TypeAttribute.class_)
        attr.setType(type)

    def getType(cls, source):
        attr = source.addAttribute(TypeAttribute.class_)
        return attr.type()

    def extractTokens(cls, analyzer, text):
        tokenStream = analyzer.tokenStream("contents", StringReader(text))
        term = tokenStream.addAttribute(TermAttribute.class_)
        tokens = set()
        while tokenStream.incrementToken():
            tokens.add(term.toString()[5:])
        return tokens

    
    def displayTokens(cls, analyzer, text):

        tokenStream = analyzer.tokenStream("contents", StringReader(text))
        term = tokenStream.addAttribute(TermAttribute.class_)

        while tokenStream.incrementToken():
            print "[%s]" %(term.toString()),

    def displayTokensWithPositions(cls, analyzer, text):

        stream = analyzer.tokenStream("contents", StringReader(text))
        term = stream.addAttribute(TermAttribute.class_)
        posIncr = stream.addAttribute(PositionIncrementAttribute.class_)

        position = 0
        while stream.incrementToken():
            increment = posIncr.getPositionIncrement()
            if increment > 0:
                position = position + increment
                print "\n%d:" %(position),

            print "[%s]" %(term.toString()),
        print

    def displayTokensWithFullDetails(cls, analyzer, text):

        stream = analyzer.tokenStream("contents", StringReader(text))

        term = stream.addAttribute(TermAttribute.class_)
        posIncr = stream.addAttribute(PositionIncrementAttribute.class_)
        offset = stream.addAttribute(OffsetAttribute.class_)
        type = stream.addAttribute(TypeAttribute.class_)

        position = 0
        while stream.incrementToken():
            increment = posIncr.getPositionIncrement()
            if increment > 0:
                position = position + increment
                print "\n%d:" %(position),

            print "[%s:%d->%d:%s]" %(term.toString(),
                                     offset.startOffset(),
                                     offset.endOffset(),
                                     type.type()),
        print

    def assertAnalyzesTo(cls, analyzer, input, outputs):

        stream = analyzer.tokenStream("field", StringReader(input))
        termAttr = stream.addAttribute(TermAttribute.class_)
        for output in outputs:
            if not stream.incrementToken():
                raise AssertionError, 'stream.incremementToken()'
            if output != termAttr.toString():
                raise AssertionError, 'output == termAttr.toString())'

        if stream.incrementToken():
            raise AssertionError, 'not stream.incremementToken()'

        stream.close()

    main = classmethod(main)
    setPositionIncrement = classmethod(setPositionIncrement)
    getPositionIncrement = classmethod(getPositionIncrement)
    setTerm = classmethod(setTerm)
    getTerm = classmethod(getTerm)
    setType = classmethod(setType)
    getType = classmethod(getType)
    extractTokens = classmethod(extractTokens)
    displayTokens = classmethod(displayTokens)
    displayTokensWithPositions = classmethod(displayTokensWithPositions)
    displayTokensWithFullDetails = classmethod(displayTokensWithFullDetails)
    assertAnalyzesTo = classmethod(assertAnalyzesTo)


if __name__ == "__main__":
    import sys
    WikiAnalyzerUtils.main(sys.argv)
