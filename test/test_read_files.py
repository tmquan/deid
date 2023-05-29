import difflib
from deid.utils import read_files
from deid.utils import html_diffs

# Test case
def test_read_files():
    csvs = read_files(["data/6294"], "csv", "Doctor's Note")
    txts = read_files(["data/6295"], "txt", None)

    print(csvs)
    print(txts)
    # difference = difflib.HtmlDiff(tabsize=2)

    with open("test_read_files.html", "w") as fp:
        for csv, txt in zip(csvs, txts):
            # html = difference.make_file(
            #     fromlines=csvs, 
            #     tolines=txts, 
            #     fromdesc="csv", 
            #     todesc="txt")
            html = html_diffs(csv, txt)
            fp.write(html)
