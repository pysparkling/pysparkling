from __future__ import print_function

import logging
from nose.plugins.skip import SkipTest
import os
import pickle
from pysparkling import Context
from pysparkling.fileio import File
import random
import sys
import tempfile
import unittest

try:
    import py7zlib
except ImportError:
    py7zlib = None

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
S3_TEST_PATH = os.getenv('S3_TEST_PATH')
OAUTH2_CLIENT_ID = os.getenv('OAUTH2_CLIENT_ID')
GS_TEST_PATH = os.getenv('GS_TEST_PATH')
HDFS_TEST_PATH = os.getenv('HDFS_TEST_PATH')
LOCAL_TEST_PATH = os.path.dirname(__file__)


def test_cache():
    # this crashes in version 0.2.28
    lines = Context().textFile('{}/*textFil*.py'.format(LOCAL_TEST_PATH))
    lines = lines.map(lambda l: '-' + l).cache()
    print(len(lines.collect()))
    lines = lines.map(lambda l: '+' + l)
    lines = lines.map(lambda l: '-' + l).cache()
    lines = lines.collect()
    print(lines)
    assert '-+-from pysparkling import Context' in lines


def test_local_textFile_1():
    lines = Context().textFile('{}/*textFil*.py'.format(LOCAL_TEST_PATH))
    lines = lines.collect()
    print(lines)
    assert 'from pysparkling import Context' in lines


def test_local_textFile_2():
    line_count = Context().textFile('{}/*.py'.format(LOCAL_TEST_PATH)).count()
    print(line_count)
    assert line_count > 90


def test_local_textFile_name():
    name = Context().textFile('{}/*.py'.format(LOCAL_TEST_PATH)).name()
    print(name)
    assert name.startswith('{}/*.py'.format(LOCAL_TEST_PATH))


def test_wholeTextFiles():
    all_files = Context().wholeTextFiles('{}/*.py'.format(LOCAL_TEST_PATH))
    this_file = all_files.lookup(__file__)
    print(this_file)
    assert 'test_wholeTextFiles' in this_file[0]


def test_s3_textFile():
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        raise SkipTest

    myrdd = Context().textFile(
        's3n://aws-publicdatasets/common-crawl/crawl-data/'
        'CC-MAIN-2015-11/warc.paths.*'
    )
    assert (
        'common-crawl/crawl-data/CC-MAIN-2015-11/segments/1424937481488.49/'
        'warc/CC-MAIN-20150226075801-00329-ip-10-28-5-156.ec2.'
        'internal.warc.gz' in myrdd.collect()
    )


def test_s3_textFile_loop():
    if not AWS_ACCESS_KEY_ID or not S3_TEST_PATH:
        raise SkipTest

    random.seed()

    fn = '{}/pysparkling_test_{0}.txt'.format(
        S3_TEST_PATH, int(random.random() * 999999.0)
    )

    rdd = Context().parallelize('Line {0}'.format(n) for n in range(200))
    rdd.saveAsTextFile(fn)
    rdd_check = Context().textFile(fn)

    assert (
        rdd.count() == rdd_check.count() and
        all(e1 == e2 for e1, e2 in zip(rdd.collect(), rdd_check.collect()))
    )


def test_hdfs_textFile_loop():
    if not HDFS_TEST_PATH:
        raise SkipTest

    random.seed()

    fn = '{}/pysparkling_test_{0}.txt'.format(
        HDFS_TEST_PATH, int(random.random() * 999999.0)
    )
    print('HDFS test file: {0}'.format(fn))

    rdd = Context().parallelize('Hello World {0}'.format(x) for x in range(10))
    rdd.saveAsTextFile(fn)
    read_rdd = Context().textFile(fn)
    print(rdd.collect())
    print(read_rdd.collect())
    assert (
        rdd.count() == read_rdd.count() and
        all(r1 == r2 for r1, r2 in zip(rdd.collect(), read_rdd.collect()))
    )


def test_hdfs_file_exists():
    if not HDFS_TEST_PATH:
        raise SkipTest

    random.seed()

    fn1 = '{}/pysparkling_test_{0}.txt'.format(
        HDFS_TEST_PATH, int(random.random() * 999999.0)
    )
    fn2 = '{}/pysparkling_test_{0}.txt'.format(
        HDFS_TEST_PATH, int(random.random() * 999999.0)
    )

    rdd = Context().parallelize('Hello World {0}'.format(x) for x in range(10))
    rdd.saveAsTextFile(fn1)

    assert File(fn1).exists() and not File(fn2).exists()


def test_gs_textFile_loop():
    if not OAUTH2_CLIENT_ID or not GS_TEST_PATH:
        raise SkipTest

    random.seed()

    fn = '{}/pysparkling_test_{0}.txt'.format(
        GS_TEST_PATH, int(random.random() * 999999.0)
    )

    rdd = Context().parallelize('Line {0}'.format(n) for n in range(200))
    rdd.saveAsTextFile(fn)
    rdd_check = Context().textFile(fn)

    assert (
        rdd.count() == rdd_check.count() and
        all(e1 == e2 for e1, e2 in zip(rdd.collect(), rdd_check.collect()))
    )


def test_dumpToFile():
    if not AWS_ACCESS_KEY_ID or not S3_TEST_PATH:
        raise SkipTest

    random.seed()

    fn = '{}/pysparkling_test_{0}.pickle'.format(
        S3_TEST_PATH, int(random.random() * 999999.0)
    )
    File(fn).dump(pickle.dumps({'hello': 'world'}))


def test_http_textFile():
    myrdd = Context().textFile(
        'https://s3-us-west-2.amazonaws.com/human-microbiome-project/DEMO/'
        'HM16STR/46333/by_subject/1139.fsa'
    )
    assert u'TGCTGCGGTGAATGCGTTCCCGGGTCT' in myrdd.collect()


def test_saveAsTextFile():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name)
    with open(tempFile.name, 'r') as f:
        r = f.readlines()
        print(r)
        assert '5\n' in r


def test_saveAsTextFile_tar():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.tar')
    read_rdd = Context().textFile(tempFile.name + '.tar')
    print(read_rdd.collect())
    assert '5' in read_rdd.collect()


@unittest.skipIf(hasattr(sys, 'pypy_version_info'), 'skip on pypy')
def test_saveAsTextFile_targz():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.tar.gz')
    read_rdd = Context().textFile(tempFile.name + '.tar.gz')
    print(read_rdd.collect())
    assert '5' in read_rdd.collect()


def test_saveAsTextFile_tarbz2():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.tar.bz2')
    read_rdd = Context().textFile(tempFile.name + '.tar.bz2')
    print(read_rdd.collect())
    assert '5' in read_rdd.collect()


def test_saveAsTextFile_gz():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.gz')
    read_rdd = Context().textFile(tempFile.name + '.gz')
    assert '5' in read_rdd.collect()


def test_saveAsTextFile_zip():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.zip')
    read_rdd = Context().textFile(tempFile.name + '.zip')
    print(read_rdd.collect())
    assert '5' in read_rdd.collect()


def test_saveAsTextFile_bz2():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.bz2')
    read_rdd = Context().textFile(tempFile.name + '.bz2')
    assert '5' in read_rdd.collect()


def test_saveAsTextFile_lzma():
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(10)).saveAsTextFile(tempFile.name + '.lzma')
    read_rdd = Context().textFile(tempFile.name + '.lzma')
    assert '5' in read_rdd.collect()


@unittest.skipIf(py7zlib is None,
                 'py7zlib import failed, is pylzma installed?')
def test_read_7z():
    # file was created with:
    # 7z a tests/data.7z tests/readme_example.py
    # (brew install p7zip)
    rdd = Context().textFile('{}/data.7z'.format(LOCAL_TEST_PATH))
    print(rdd.collect())
    assert 'from pysparkling import Context' in rdd.collect()


def test_read_tar_gz():
    # file was created with:
    # tar -cvzf data.tar.gz hello.txt
    rdd = Context().textFile('{}/data.tar.gz'.format(LOCAL_TEST_PATH))
    print(rdd.collect())
    assert 'Hello pysparkling!' in rdd.collect()


@unittest.skipIf(os.getenv('TRAVIS', False) is not False,
                 'skip 20news test on Travis')
def test_read_tar_gz_20news():
    # 20 news dataset has some '0xff' characters that lead to encoding
    # errors before. Adding this as a test case.
    src = 'http://qwone.com/~jason/20Newsgroups/20news-19997.tar.gz'
    rdd = Context().textFile(src, use_unicode=False)
    assert '}|> 1. Mechanical driven odometer:' in rdd.top(500)


def test_pyspark_compatibility_txt():
    kv = Context().textFile(
        '{}/pyspark/key_value.txt'.format(LOCAL_TEST_PATH)).collect()
    print(kv)
    assert u"('a', 1)" in kv and u"('b', 2)" in kv and len(kv) == 2


def test_pyspark_compatibility_bz2():
    kv = Context().textFile(
        '{}/pyspark/key_value.txt.bz2'.format(LOCAL_TEST_PATH)).collect()
    print(kv)
    assert u"a\t1" in kv and u"b\t2" in kv and len(kv) == 2


def test_pyspark_compatibility_gz():
    kv = Context().textFile(
        '{}/pyspark/key_value.txt.gz'.format(LOCAL_TEST_PATH)).collect()
    print(kv)
    assert u"a\t1" in kv and u"b\t2" in kv and len(kv) == 2


def test_local_regex_read():
    # was not working before 0.3.19
    tempFile = tempfile.NamedTemporaryFile(delete=True)
    tempFile.close()
    Context().parallelize(range(30), 30).saveAsTextFile(tempFile.name)
    d = Context().textFile(tempFile.name + '/part-0000*').collect()
    print(d)
    assert len(d) == 10


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_local_regex_read()
