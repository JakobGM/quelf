from droppboks import File as dbx_file

def test_file_retrieval():
    assert dbx_file('test.txt').read() == 'just one single line\nAnd a second one\n'
