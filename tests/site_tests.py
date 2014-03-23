# -*- coding: utf-8  -*-
"""
Tests for the site module.
"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import pywikibot
from pywikibot.site import must_be
from tests import patch_request, unpatch_request
from utils import PywikibotTestCase, unittest

mysite = None
mainpage = None
imagepage = None


class TestSiteObject(PywikibotTestCase):
    """Test cases for Site methods."""
    family = "wikipedia"
    code = "en"

    @classmethod
    def setUpClass(cls):
        global mysite, mainpage, imagepage
        mysite = pywikibot.Site(cls.code, cls.family)
        mainpage = pywikibot.Page(pywikibot.Link("Main Page", mysite))
        imagepage = next(iter(mainpage.imagelinks()))  # 1st image on main page

    def testBaseMethods(self):
        """Test cases for BaseSite methods"""
        self.assertEqual(mysite.family.name, self.family)
        self.assertEqual(mysite.code, self.code)
        self.assertType(mysite.lang, basestring)
        self.assertEqual(mysite, pywikibot.Site("en", "wikipedia"))
        self.assertType(mysite.user(), (basestring, type(None)))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (self.family,
                                    self.code))
        self.assertEqual(repr(mysite),
                         'Site("%s", "%s")'
                         % (self.code, self.family))
        self.assertType(mysite.linktrail(), basestring)
        self.assertType(mysite.redirect(default=True), basestring)
        self.assertType(mysite.disambcategory(), pywikibot.Category)
        self.assertEqual(mysite.linkto("foo"), u"[[Foo]]")  # deprecated
        self.assertFalse(mysite.isInterwikiLink("foo"))
        self.assertType(mysite.redirectRegex().pattern, basestring)
        self.assertType(mysite.category_on_one_line(), bool)
        for grp in ("user", "autoconfirmed", "bot", "sysop", "nosuchgroup"):
            self.assertType(mysite.has_group(grp), bool)
        for rgt in ("read", "edit", "move", "delete", "rollback", "block",
                    "nosuchright"):
            self.assertType(mysite.has_right(rgt), bool)

    def testConstructors(self):
        """Test cases for site constructors"""
        self.assertEqual(pywikibot.site.APISite.fromDBName('enwiki'), pywikibot.Site('en', 'wikipedia'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('eswikisource'), pywikibot.Site('es', 'wikisource'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('dewikinews'), pywikibot.Site('de', 'wikinews'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('ukwikivoyage'), pywikibot.Site('uk', 'wikivoyage'))

        self.assertRaises(ValueError, pywikibot.site.APISite.fromDBName, 'metawiki')

    def testLanguageMethods(self):
        """Test cases for languages() and related methods"""

        langs = mysite.languages()
        self.assertType(langs, list)
        self.assertTrue(mysite.code in langs)
        obs = mysite.family.obsolete
        ipf = mysite.interwiki_putfirst()
        if ipf:  # Not all languages use this
            self.assertType(ipf, list)

        for item in mysite.validLanguageLinks():
            self.assertTrue(item in langs, item)

    def testNamespaceMethods(self):
        """Test cases for methods manipulating namespace names"""

        builtins = {
            'Talk': 1,  # these should work in any MW wiki
            'User': 2,
            'User talk': 3,
            'Project': 4,
            'Project talk': 5,
            'Image': 6,
            'Image talk': 7,
            'MediaWiki': 8,
            'MediaWiki talk': 9,
            'Template': 10,
            'Template talk': 11,
            'Help': 12,
            'Help talk': 13,
            'Category': 14,
            'Category talk': 15,
        }
        self.assertTrue(all(mysite.ns_index(b) == builtins[b]
                            for b in builtins))
        ns = mysite.namespaces()
        self.assertType(ns, dict)
        self.assertTrue(all(x in ns for x in range(0, 16)))
            # built-in namespaces always present
        self.assertType(mysite.ns_normalize("project"), basestring)
        self.assertTrue(all(isinstance(key, int)
                            for key in ns))
        self.assertTrue(all(isinstance(val, list)
                            for val in ns.values()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in ns.values()
                            for name in val))
        self.assertTrue(all(isinstance(mysite.namespace(key), basestring)
                            for key in ns))
        self.assertTrue(all(isinstance(mysite.namespace(key, True), list)
                            for key in ns))
        self.assertTrue(all(isinstance(item, basestring)
                            for key in ns
                            for item in mysite.namespace(key, True)))

    def testApiMethods(self):
        """Test generic ApiSite methods"""

        self.assertType(mysite.logged_in(), bool)
        self.assertType(mysite.logged_in(True), bool)
        self.assertType(mysite.userinfo, dict)
        self.assertType(mysite.is_blocked(), bool)
        self.assertType(mysite.messages(), bool)
        self.assertType(mysite.has_right("edit"), bool)
        self.assertFalse(mysite.has_right("nonexistent_right"))
        self.assertType(mysite.has_group("bots"), bool)
        self.assertFalse(mysite.has_group("nonexistent_group"))
        try:
            self.assertType(mysite.is_blocked(True), bool)
            self.assertType(mysite.has_right("edit", True), bool)
            self.assertFalse(mysite.has_right("nonexistent_right", True))
            self.assertType(mysite.has_group("bots", True), bool)
            self.assertFalse(mysite.has_group("nonexistent_group", True))
        except pywikibot.NoUsername:
            pywikibot.warning(
                "Cannot test Site methods for sysop; no sysop account configured.")

        for msg in ("1movedto2", "about", "aboutpage", "aboutsite",
                    "accesskey-n-portal"):
            self.assertTrue(mysite.has_mediawiki_message(msg))
            self.assertType(mysite.mediawiki_message(msg), basestring)
        self.assertFalse(mysite.has_mediawiki_message("nosuchmessage"))
        self.assertRaises(KeyError, mysite.mediawiki_message, "nosuchmessage")

        msg = ("1movedto2", "about", "aboutpage")
        self.assertType(mysite.mediawiki_messages(msg), dict)
        self.assertTrue(mysite.mediawiki_messages(msg))

        msg = ("nosuchmessage1", "about", "aboutpage", "nosuchmessage")
        self.assertFalse(mysite.has_all_mediawiki_messages(msg))
        self.assertRaises(KeyError, mysite.mediawiki_messages, msg)

        # Load all messages and check that '*' is not a valid key.
        self.assertType(mysite.mediawiki_messages('*'), dict)
        self.assertTrue(len(mysite.mediawiki_messages(['*'])) > 10)
        self.assertFalse('*' in mysite.mediawiki_messages(['*']))

        self.assertType(mysite.getcurrenttimestamp(), basestring)
        self.assertType(mysite.siteinfo, dict)
        self.assertType(mysite.case(), basestring)
        ver = mysite.live_version()
        self.assertType(ver, tuple)
        self.assertTrue(all(isinstance(ver[i], int) for i in (0, 1)))
        self.assertType(ver[2], basestring)
        self.assertType(mysite.months_names, list)
        self.assertEqual(mysite.months_names[4], (u'May', u'May'))

    def testPageMethods(self):
        """Test ApiSite methods for getting page-specific info"""

        self.assertType(mysite.page_exists(mainpage), bool)
        self.assertType(mysite.page_restrictions(mainpage), dict)
        self.assertType(mysite.page_can_be_edited(mainpage), bool)
        self.assertType(mysite.page_isredirect(mainpage), bool)
        if mysite.page_isredirect(mainpage):
            self.assertType(mysite.getredirtarget(mainpage), pywikibot.Page)
        else:
            self.assertRaises(pywikibot.IsNotRedirectPage,
                              mysite.getredirtarget, mainpage)
        a = list(mysite.preloadpages([mainpage]))
        self.assertEqual(len(a), int(mysite.page_exists(mainpage)))
        if a:
            self.assertEqual(a[0], mainpage)

    def testTokens(self):
        """Test ability to get page tokens"""

        for ttype in ("edit", "move"):  # token types for non-sysops
            self.assertType(mysite.token(mainpage, ttype), basestring)
        self.assertRaises(KeyError, mysite.token, mainpage, "invalidtype")

    def testPreload(self):
        """Test that preloading works"""

        count = 0
        for page in mysite.preloadpages(mysite.pagelinks(mainpage, total=10)):
            self.assertType(page, pywikibot.Page)
            self.assertType(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, "_text"))
            count += 1
            if count >= 5:
                break

    def testItemPreload(self):
        """Test that ItemPage preloading works"""

        datasite = mysite.data_repository()

        items = [pywikibot.ItemPage(datasite, 'q' + str(num)) for num in range(1, 6)]
        for page in datasite.preloaditempages(items):
            self.assertTrue(hasattr(page, '_content'))

    def testLinkMethods(self):
        """Test site methods for getting links to and from a page"""

        backlinks = set(mysite.pagebacklinks(mainpage, namespaces=[0]))
        # only non-redirects:
        filtered = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                            filterRedirects=False))
        # only redirects:
        redirs = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                          filterRedirects=True))
        # including links to redirect pages (but not the redirects):
        indirect = set(mysite.pagebacklinks(mainpage, namespaces=[0],
                                            followRedirects=True,
                                            filterRedirects=False))
        self.assertEqual(filtered & redirs, set([]))
        self.assertEqual(indirect & redirs, set([]))
        self.assertTrue(filtered.issubset(indirect))
        self.assertTrue(filtered.issubset(backlinks))
        self.assertTrue(redirs.issubset(backlinks))
        self.assertTrue(backlinks.issubset(
                        set(mysite.pagebacklinks(mainpage, namespaces=[0, 2]))))

        # pagereferences includes both backlinks and embeddedin
        embedded = set(mysite.page_embeddedin(mainpage, namespaces=[0]))
        refs = set(mysite.pagereferences(mainpage, namespaces=[0]))
        self.assertTrue(backlinks.issubset(refs))
        self.assertTrue(embedded.issubset(refs))
        for bl in backlinks:
            self.assertType(bl, pywikibot.Page)
            self.assertTrue(bl in refs)
        for ei in embedded:
            self.assertType(ei, pywikibot.Page)
            self.assertTrue(ei in refs)
        for ref in refs:
            self.assertTrue(ref in backlinks or ref in embedded)
        # test embeddedin arguments
        self.assertTrue(embedded.issuperset(
            set(mysite.page_embeddedin(mainpage, filterRedirects=True,
                                       namespaces=[0]))))
        self.assertTrue(embedded.issuperset(
            set(mysite.page_embeddedin(mainpage, filterRedirects=False,
                                       namespaces=[0]))))
        self.assertTrue(embedded.issubset(
            set(mysite.page_embeddedin(mainpage, namespaces=[0, 2]))))
        links = set(mysite.pagelinks(mainpage))
        for pl in links:
            self.assertType(pl, pywikibot.Page)
        # test links arguments
        self.assertTrue(links.issuperset(
            set(mysite.pagelinks(mainpage, namespaces=[0, 1]))))
        for target in mysite.preloadpages(mysite.pagelinks(mainpage,
                                                           follow_redirects=True,
                                                           total=5)):
            self.assertType(target, pywikibot.Page)
            self.assertFalse(target.isRedirectPage())
        # test pagecategories
        for cat in mysite.pagecategories(mainpage):
            self.assertType(cat, pywikibot.Category)
            for cm in mysite.categorymembers(cat):
                self.assertType(cat, pywikibot.Page)
        # test pageimages
        self.assertTrue(all(isinstance(im, pywikibot.ImagePage)
                            for im in mysite.pageimages(mainpage)))
        # test pagetemplates
        self.assertTrue(all(isinstance(te, pywikibot.Page)
                            for te in mysite.pagetemplates(mainpage)))
        self.assertTrue(set(mysite.pagetemplates(mainpage)).issuperset(
                        set(mysite.pagetemplates(mainpage, namespaces=[10]))))
        # test pagelanglinks
        for ll in mysite.pagelanglinks(mainpage):
            self.assertType(ll, pywikibot.Link)
        # test page_extlinks
        self.assertTrue(all(isinstance(el, basestring)
                            for el in mysite.page_extlinks(mainpage)))

    def testAllPages(self):
        """Test the site.allpages() method"""

        fwd = list(mysite.allpages(total=10))
        self.assertTrue(len(fwd) <= 10)
        for page in fwd:
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        rev = list(mysite.allpages(reverse=True, start="Aa", total=12))
        self.assertTrue(len(rev) <= 12)
        for page in rev:
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() <= "Aa")
        for page in mysite.allpages(start="Py", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() >= "Py")
        for page in mysite.allpages(prefix="Pre", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Pre"))
        for page in mysite.allpages(namespace=1, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 1)
        for page in mysite.allpages(filterredir=True, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.isRedirectPage())
        for page in mysite.allpages(filterredir=False, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertFalse(page.isRedirectPage())
##        for page in mysite.allpages(filterlanglinks=True, total=5):
##            self.assertType(page, pywikibot.Page)
##            self.assertTrue(mysite.page_exists(page))
##            self.assertEqual(page.namespace(), 0)
##        for page in mysite.allpages(filterlanglinks=False, total=5):
##            self.assertType(page, pywikibot.Page)
##            self.assertTrue(mysite.page_exists(page))
##            self.assertEqual(page.namespace(), 0)
        for page in mysite.allpages(minsize=100, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue(len(page.text) >= 100)
        for page in mysite.allpages(maxsize=200, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue(len(page.text) <= 200)
        for page in mysite.allpages(protect_type="edit", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue("edit" in page._protection)
        for page in mysite.allpages(protect_type="edit",
                                    protect_level="sysop", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue("edit" in page._protection)
            self.assertTrue("sysop" in page._protection["edit"])

    def testAllLinks(self):
        """Test the site.alllinks() method"""

        fwd = list(mysite.alllinks(total=10))
        self.assertTrue(len(fwd) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in fwd))
        uniq = list(mysite.alllinks(total=10, unique=True))
        self.assertTrue(all(link in uniq for link in fwd))
        for page in mysite.alllinks(start="Link", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() >= "Link")
        for page in mysite.alllinks(prefix="Fix", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Fix"))
        for page in mysite.alllinks(namespace=1, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 1)
        for page in mysite.alllinks(start="From", namespace=4, fromids=True,
                                    total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(page.title(withNamespace=False) >= "From")
            self.assertTrue(hasattr(page, "_fromid"))
        errgen = mysite.alllinks(unique=True, fromids=True)
        self.assertRaises(pywikibot.Error, errgen.next)

    def testAllCategories(self):
        """Test the site.allcategories() method"""

        ac = list(mysite.allcategories(total=10))
        self.assertTrue(len(ac) <= 10)
        self.assertTrue(all(isinstance(cat, pywikibot.Category)
                            for cat in ac))
        for cat in mysite.allcategories(total=5, start="Abc"):
            self.assertType(cat, pywikibot.Category)
            self.assertTrue(cat.title(withNamespace=False) >= "Abc")
        for cat in mysite.allcategories(total=5, prefix="Def"):
            self.assertType(cat, pywikibot.Category)
            self.assertTrue(cat.title(withNamespace=False).startswith("Def"))
##        # Bug # 15985
##        for cat in mysite.allcategories(total=5, start="Hij", reverse=True):
##            self.assertType(cat, pywikibot.Category)
##            self.assertTrue(cat.title(withNamespace=False) <= "Hij")

    def testAllUsers(self):
        """Test the site.allusers() method"""

        au = list(mysite.allusers(total=10))
        self.assertTrue(len(au) <= 10)
        for user in au:
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
        for user in mysite.allusers(start="B", total=5):
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue(user["name"] >= "B")
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
        for user in mysite.allusers(prefix="C", total=5):
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue(user["name"].startswith("C"))
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
        for user in mysite.allusers(prefix="D", group="sysop", total=5):
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue(user["name"].startswith("D"))
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
            self.assertTrue("groups" in user and "sysop" in user["groups"])

    def testAllImages(self):
        """Test the site.allimages() method"""

        ai = list(mysite.allimages(total=10))
        self.assertTrue(len(ai) <= 10)
        self.assertTrue(all(isinstance(image, pywikibot.ImagePage)
                            for image in ai))
        for impage in mysite.allimages(start="Ba", total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage.title(withNamespace=False) >= "Ba")
##        # Bug # 15985
##        for impage in mysite.allimages(start="Da", reverse=True, total=5):
##            self.assertType(impage, pywikibot.ImagePage)
##            self.assertTrue(mysite.page_exists(impage))
##            self.assertTrue(impage.title() <= "Da")
        for impage in mysite.allimages(prefix="Ch", total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage.title(withNamespace=False).startswith("Ch"))
        for impage in mysite.allimages(minsize=100, total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage._imageinfo["size"] >= 100)
        for impage in mysite.allimages(maxsize=2000, total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage._imageinfo["size"] <= 2000)

    def testBlocks(self):
        """Test the site.blocks() method"""

        props = ("id", "by", "timestamp", "expiry", "reason")
        bl = list(mysite.blocks(total=10))
        self.assertTrue(len(bl) <= 10)
        for block in bl:
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        # timestamps should be in descending order
        timestamps = [block['timestamp'] for block in bl]
        for t in range(1, len(timestamps)):
            self.assertTrue(timestamps[t] <= timestamps[t - 1])

        b2 = list(mysite.blocks(total=10, reverse=True))
        self.assertTrue(len(b2) <= 10)
        for block in b2:
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        # timestamps should be in ascending order
        timestamps = [block['timestamp'] for block in b2]
        for t in range(1, len(timestamps)):
            self.assertTrue(timestamps[t] >= timestamps[t - 1])

        for block in mysite.blocks(starttime="2008-07-01T00:00:01Z", total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        for block in mysite.blocks(endtime="2008-07-31T23:59:59Z", total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        for block in mysite.blocks(starttime="2008-08-02T00:00:01Z",
                                   endtime="2008-08-02T23:59:59Z",
                                   reverse=True, total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        for block in mysite.blocks(starttime="2008-08-03T23:59:59Z",
                                   endtime="2008-08-03T00:00:01Z",
                                   total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime="2008-08-03T00:00:01Z",
                          endtime="2008-08-03T23:59:59Z", total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime="2008-08-03T23:59:59Z",
                          endtime="2008-08-03T00:00:01Z", reverse=True, total=5)
        for block in mysite.blocks(users=mysite.user(), total=5):
            self.assertType(block, dict)
            self.assertEqual(block['user'], mysite.user())

    def testExturlusage(self):
        """Test the site.exturlusage() method"""

        url = "www.google.com"
        eu = list(mysite.exturlusage(url, total=10))
        self.assertTrue(len(eu) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in eu))
        for link in mysite.exturlusage(url, namespaces=[2, 3], total=5):
            self.assertType(link, pywikibot.Page)
            self.assertTrue(link.namespace() in (2, 3))

    def testImageusage(self):
        """Test the site.imageusage() method"""

        iu = list(mysite.imageusage(imagepage, total=10))
        self.assertTrue(len(iu) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in iu))
        for using in mysite.imageusage(imagepage, namespaces=[3, 4], total=5):
            self.assertType(using, pywikibot.Page)
            self.assertTrue(imagepage in list(using.imagelinks()))
        for using in mysite.imageusage(imagepage, filterredir=True, total=5):
            self.assertType(using, pywikibot.Page)
            self.assertTrue(using.isRedirectPage())
        for using in mysite.imageusage(imagepage, filterredir=False, total=5):
            self.assertType(using, pywikibot.Page)
            self.assertFalse(using.isRedirectPage())

    def testLogEvents(self):
        """Test the site.logevents() method"""

        le = list(mysite.logevents(total=10))
        self.assertTrue(len(le) <= 10)
        self.assertTrue(all(isinstance(entry, pywikibot.logentries.LogEntry)
                            for entry in le))
        for typ in ("block", "protect", "rights", "delete", "upload",
                    "move", "import", "patrol", "merge"):
            for entry in mysite.logevents(logtype=typ, total=3):
                self.assertEqual(entry.type(), typ)
        for entry in mysite.logevents(page=mainpage, total=3):
            self.assertTrue(entry.title().title() == mainpage.title())
        for entry in mysite.logevents(user=mysite.user(), total=3):
            self.assertTrue(entry.user() == mysite.user())
        for entry in mysite.logevents(start="2008-09-01T00:00:01Z", total=5):
            self.assertType(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(str(entry.timestamp()) <= "2008-09-01T00:00:01Z")
        for entry in mysite.logevents(end="2008-09-02T23:59:59Z", total=5):
            self.assertType(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(str(entry.timestamp()) >= "2008-09-02T23:59:59Z")
        for entry in mysite.logevents(start="2008-02-02T00:00:01Z",
                                      end="2008-02-02T23:59:59Z",
                                      reverse=True, total=5):
            self.assertType(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                "2008-02-02T00:00:01Z" <= str(entry.timestamp()) <= "2008-02-02T23:59:59Z")
        for entry in mysite.logevents(start="2008-02-03T23:59:59Z",
                                      end="2008-02-03T00:00:01Z",
                                      total=5):
            self.assertType(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                "2008-02-03T00:00:01Z" <= str(entry.timestamp()) <= "2008-02-03T23:59:59Z")
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.logevents,
                          start="2008-02-03T00:00:01Z",
                          end="2008-02-03T23:59:59Z", total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.logevents,
                          start="2008-02-03T23:59:59Z",
                          end="2008-02-03T00:00:01Z", reverse=True, total=5)

    def testRecentchanges(self):
        """Test the site.recentchanges() method"""

        rc = list(mysite.recentchanges(total=10))
        self.assertTrue(len(rc) <= 10)
        self.assertTrue(all(isinstance(change, dict)
                            for change in rc))
        for change in mysite.recentchanges(start="2008-10-01T01:02:03Z",
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] <= "2008-10-01T01:02:03Z")
        for change in mysite.recentchanges(end="2008-04-01T02:03:04Z",
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] >= "2008-10-01T02:03:04Z")
        for change in mysite.recentchanges(start="2008-10-01T03:05:07Z",
                                           total=5, reverse=True):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] >= "2008-10-01T03:05:07Z")
        for change in mysite.recentchanges(end="2008-10-01T04:06:08Z",
                                           total=5, reverse=True):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] <= "2008-10-01T04:06:08Z")
        for change in mysite.recentchanges(start="2008-10-03T11:59:59Z",
                                           end="2008-10-03T00:00:01Z",
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue(
                "2008-10-03T00:00:01Z" <= change['timestamp'] <= "2008-10-03T11:59:59Z")
        for change in mysite.recentchanges(start="2008-10-05T06:00:01Z",
                                           end="2008-10-05T23:59:59Z",
                                           reverse=True, total=5):
            self.assertType(change, dict)
            self.assertTrue(
                "2008-10-05T06:00:01Z" <= change['timestamp'] <= "2008-10-05T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T00:00:01Z",
                          end="2008-02-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T23:59:59Z",
                          end="2008-02-03T00:00:01Z", reverse=True, total=5)
        for change in mysite.recentchanges(namespaces=[6, 7], total=5):
            self.assertType(change, dict)
            self.assertTrue("title" in change and "ns" in change)
            title = change['title']
            self.assertTrue(":" in title)
            prefix = title[:title.index(":")]
            self.assertTrue(mysite.ns_index(prefix) in [6, 7])
            self.assertTrue(change["ns"] in [6, 7])
        if mysite.versionnumber() <= 14:
            for change in mysite.recentchanges(pagelist=[mainpage, imagepage],
                                               total=5):
                self.assertType(change, dict)
                self.assertTrue("title" in change)
                self.assertTrue(change["title"] in (mainpage.title(),
                                                    imagepage.title()))
        for typ in ("edit", "new", "log"):
            for change in mysite.recentchanges(changetype=typ, total=5):
                self.assertType(change, dict)
                self.assertTrue("type" in change)
                self.assertEqual(change["type"], typ)
        for change in mysite.recentchanges(showMinor=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("minor" in change)
        for change in mysite.recentchanges(showMinor=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("minor" not in change)
        for change in mysite.recentchanges(showBot=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("bot" in change)
        for change in mysite.recentchanges(showBot=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("bot" not in change)
        for change in mysite.recentchanges(showAnon=True, total=5):
            self.assertType(change, dict)
        for change in mysite.recentchanges(showAnon=False, total=5):
            self.assertType(change, dict)
        for change in mysite.recentchanges(showRedirects=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("redirect" in change)
        for change in mysite.recentchanges(showRedirects=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("redirect" not in change)
        for change in mysite.recentchanges(showPatrolled=True, total=5):
            self.assertType(change, dict)
            if mysite.has_right('patrol'):
                self.assertTrue("patrolled" in change)
        for change in mysite.recentchanges(showPatrolled=False, total=5):
            self.assertType(change, dict)
            if mysite.has_right('patrol'):
                self.assertTrue("patrolled" not in change)

    def testSearch(self):
        """Test the site.search() method"""
        try:
            se = list(mysite.search("wiki", total=10))
            self.assertTrue(len(se) <= 10)
            self.assertTrue(all(isinstance(hit, pywikibot.Page)
                                for hit in se))
            self.assertTrue(all(hit.namespace() == 0 for hit in se))
            for hit in mysite.search("common", namespaces=4, total=5):
                self.assertType(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 4)
            for hit in mysite.search("word", namespaces=[5, 6, 7], total=5):
                self.assertType(hit, pywikibot.Page)
                self.assertTrue(hit.namespace() in [5, 6, 7])
            for hit in mysite.search("another", namespaces="8|9|10", total=5):
                self.assertType(hit, pywikibot.Page)
                self.assertTrue(hit.namespace() in [8, 9, 10])
            for hit in mysite.search("wiki", namespaces=0, total=10,
                                     getredirects=True):
                self.assertType(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
        except pywikibot.data.api.APIError as e:
            if e.code == "gsrsearch-error" and "timed out" in e.info:
                raise unittest.SkipTest("gsrsearch returned timeout on site: %r" % e)
            raise

    def testUsercontribs(self):
        """Test the site.usercontribs() method"""

        uc = list(mysite.usercontribs(user=mysite.user(), total=10))
        self.assertTrue(len(uc) <= 10)
        self.assertTrue(all(isinstance(contrib, dict)
                            for contrib in uc))
        self.assertTrue(all("user" in contrib
                            and contrib["user"] == mysite.user()
                            for contrib in uc))
        for contrib in mysite.usercontribs(userprefix="John", total=5):
            self.assertType(contrib, dict)
            for key in ("user", "title", "ns", "pageid", "revid"):
                self.assertTrue(key in contrib)
            self.assertTrue(contrib["user"].startswith("John"))
        for contrib in mysite.usercontribs(userprefix="Jane",
                                           start="2008-10-06T01:02:03Z",
                                           total=5):
            self.assertTrue(contrib['timestamp'] <= "2008-10-06T01:02:03Z")
        for contrib in mysite.usercontribs(userprefix="Jane",
                                           end="2008-10-07T02:03:04Z",
                                           total=5):
            self.assertTrue(contrib['timestamp'] >= "2008-10-07T02:03:04Z")
        for contrib in mysite.usercontribs(userprefix="Brion",
                                           start="2008-10-08T03:05:07Z",
                                           total=5, reverse=True):
            self.assertTrue(contrib['timestamp'] >= "2008-10-08T03:05:07Z")
        for contrib in mysite.usercontribs(userprefix="Brion",
                                           end="2008-10-09T04:06:08Z",
                                           total=5, reverse=True):
            self.assertTrue(contrib['timestamp'] <= "2008-10-09T04:06:08Z")
        for contrib in mysite.usercontribs(userprefix="Tim",
                                           start="2008-10-10T11:59:59Z",
                                           end="2008-10-10T00:00:01Z",
                                           total=5):
            self.assertTrue(
                "2008-10-10T00:00:01Z" <= contrib['timestamp'] <= "2008-10-10T11:59:59Z")
        for contrib in mysite.usercontribs(userprefix="Tim",
                                           start="2008-10-11T06:00:01Z",
                                           end="2008-10-11T23:59:59Z",
                                           reverse=True, total=5):
            self.assertTrue(
                "2008-10-11T06:00:01Z" <= contrib['timestamp'] <= "2008-10-11T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.usercontribs,
                          userprefix="Jim",
                          start="2008-10-03T00:00:01Z",
                          end="2008-10-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.usercontribs,
                          userprefix="Jim",
                          start="2008-10-03T23:59:59Z",
                          end="2008-10-03T00:00:01Z", reverse=True, total=5)

        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=14, total=5):
            self.assertType(contrib, dict)
            self.assertTrue("title" in contrib)
            self.assertTrue(contrib["title"].startswith(mysite.namespace(14)))
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=[10, 11], total=5):
            self.assertType(contrib, dict)
            self.assertTrue("title" in contrib)
            self.assertTrue(contrib["ns"] in (10, 11))
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=True, total=5):
            self.assertType(contrib, dict)
            self.assertTrue("minor" in contrib)
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=False, total=5):
            self.assertType(contrib, dict)
            self.assertTrue("minor" not in contrib)

    def testWatchlistrevs(self):
        """Test the site.watchlist_revs() method"""

        wl = list(mysite.watchlist_revs(total=10))
        self.assertTrue(len(wl) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in wl))
        for rev in mysite.watchlist_revs(start="2008-10-11T01:02:03Z",
                                         total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T01:02:03Z")
        for rev in mysite.watchlist_revs(end="2008-04-01T02:03:04Z",
                                         total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T02:03:04Z")
        for rev in mysite.watchlist_revs(start="2008-10-11T03:05:07Z",
                                         total=5, reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T03:05:07Z")
        for rev in mysite.watchlist_revs(end="2008-10-11T04:06:08Z",
                                         total=5, reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T04:06:08Z")
        for rev in mysite.watchlist_revs(start="2008-10-13T11:59:59Z",
                                         end="2008-10-13T00:00:01Z",
                                         total=5):
            self.assertType(rev, dict)
            self.assertTrue(
                "2008-10-13T00:00:01Z" <= rev['timestamp'] <= "2008-10-13T11:59:59Z")
        for rev in mysite.watchlist_revs(start="2008-10-15T06:00:01Z",
                                         end="2008-10-15T23:59:59Z",
                                         reverse=True, total=5):
            self.assertType(rev, dict)
            self.assertTrue(
                "2008-10-15T06:00:01Z" <= rev['timestamp'] <= "2008-10-15T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True, total=5)
        for rev in mysite.watchlist_revs(namespaces=[6, 7], total=5):
            self.assertType(rev, dict)
            self.assertTrue("title" in rev and "ns" in rev)
            title = rev['title']
            self.assertTrue(":" in title)
            prefix = title[:title.index(":")]
            self.assertTrue(mysite.ns_index(prefix) in [6, 7])
            self.assertTrue(rev["ns"] in [6, 7])
        for rev in mysite.watchlist_revs(showMinor=True, total=5):
            self.assertType(rev, dict)
            self.assertTrue("minor" in rev)
        for rev in mysite.watchlist_revs(showMinor=False, total=5):
            self.assertType(rev, dict)
            self.assertTrue("minor" not in rev)
        for rev in mysite.watchlist_revs(showBot=True, total=5):
            self.assertType(rev, dict)
            self.assertTrue("bot" in rev)
        for rev in mysite.watchlist_revs(showBot=False, total=5):
            self.assertType(rev, dict)
            self.assertTrue("bot" not in rev)
        for rev in mysite.watchlist_revs(showAnon=True, total=5):
            self.assertType(rev, dict)
        for rev in mysite.watchlist_revs(showAnon=False, total=5):
            self.assertType(rev, dict)

    def testDeletedrevs(self):
        """Test the site.deletedrevs() method"""

        if not mysite.logged_in(True):
            try:
                mysite.login(True)
            except pywikibot.NoUsername:
                pywikibot.warning(
                    "Cannot test Site.deleted_revs; no sysop account configured.")
                return
        dr = list(mysite.deletedrevs(total=10, page=mainpage))
        self.assertTrue(len(dr) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr))
        dr2 = list(mysite.deletedrevs(page=mainpage, total=10))
        self.assertTrue(len(dr2) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr2))
        for rev in mysite.deletedrevs(start="2008-10-11T01:02:03Z",
                                      page=mainpage, total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T01:02:03Z")
        for rev in mysite.deletedrevs(end="2008-04-01T02:03:04Z",
                                      page=mainpage, total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T02:03:04Z")
        for rev in mysite.deletedrevs(start="2008-10-11T03:05:07Z",
                                      page=mainpage, total=5,
                                      reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T03:05:07Z")
        for rev in mysite.deletedrevs(end="2008-10-11T04:06:08Z",
                                      page=mainpage, total=5,
                                      reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T04:06:08Z")
        for rev in mysite.deletedrevs(start="2008-10-13T11:59:59Z",
                                      end="2008-10-13T00:00:01Z",
                                      page=mainpage, total=5):
            self.assertType(rev, dict)
            self.assertTrue(
                "2008-10-13T00:00:01Z" <= rev['timestamp'] <= "2008-10-13T11:59:59Z")
        for rev in mysite.deletedrevs(start="2008-10-15T06:00:01Z",
                                      end="2008-10-15T23:59:59Z",
                                      page=mainpage, reverse=True,
                                      total=5):
            self.assertType(rev, dict)
            self.assertTrue(
                "2008-10-15T06:00:01Z" <= rev['timestamp'] <= "2008-10-15T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.deletedrevs,
                          page=mainpage, start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.deletedrevs,
                          page=mainpage, start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True,
                          total=5)

    def testUsers(self):
        """Test the site.users() method"""

        us = list(mysite.users(mysite.user()))
        self.assertEqual(len(us), 1)
        self.assertType(us[0], dict)
        for user in mysite.users(
                ["Jimbo Wales", "Brion VIBBER", "Tim Starling"]):
            self.assertType(user, dict)
            self.assertTrue(user["name"]
                            in ["Jimbo Wales", "Brion VIBBER", "Tim Starling"])

    def testRandompages(self):
        """Test the site.randompages() method"""

        rn = list(mysite.randompages(total=10))
        self.assertTrue(len(rn) <= 10)
        self.assertTrue(all(isinstance(a_page, pywikibot.Page)
                            for a_page in rn))
        self.assertFalse(all(a_page.isRedirectPage() for a_page in rn))
        for rndpage in mysite.randompages(total=5, redirects=True):
            self.assertType(rndpage, pywikibot.Page)
            self.assertTrue(rndpage.isRedirectPage())
        for rndpage in mysite.randompages(total=5, namespaces=[6, 7]):
            self.assertType(rndpage, pywikibot.Page)
            self.assertTrue(rndpage.namespace() in [6, 7])

    def testExtensions(self):
        # test automatically getting _extensions
        del mysite._extensions
        self.assertTrue(mysite.hasExtension('Disambiguator'))

        # test case-sensitivity
        self.assertTrue(mysite.hasExtension('disambiguator'))

        self.assertFalse(mysite.hasExtension('ThisExtensionDoesNotExist'))

        # test behavior for sites that do not report extensions
        mysite._extensions = None
        self.assertRaises(NotImplementedError, mysite.hasExtension, ('anything'))

        class MyException(Exception):
            pass
        self.assertRaises(MyException, mysite.hasExtension, 'anything', MyException)

        self.assertTrue(mysite.hasExtension('anything', True))
        self.assertFalse(mysite.hasExtension('anything', False))
        del mysite._extensions

    def test_API_limits_with_site_methods(self):
        # test step/total parameters for different sitemethods
        mypage = pywikibot.Page(mysite, 'Albert Einstein')
        mycat = pywikibot.Page(mysite, 'Category:1879 births')

        cats = [c for c in mysite.pagecategories(mypage, step=5, total=12)]
        self.assertEqual(len(cats), 12)

        cat_members = [cm for cm in mysite.categorymembers(mycat, step=5, total=12)]
        self.assertEqual(len(cat_members), 12)

        images = [im for im in mysite.pageimages(mypage, step=3, total=5)]
        self.assertEqual(len(images), 5)

        templates = [tl for tl in mysite.pagetemplates(mypage, step=3, total=5)]
        self.assertEqual(len(templates), 5)

        mysite.loadrevisions(mypage, step=5, total=12)
        self.assertEqual(len(mypage._revisions), 12)


class TestSiteLoadRevisions(PywikibotTestCase):
    """Test cases for Site.loadrevision() method."""

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        code, family = "en", "wikipedia"
        self.mysite = pywikibot.Site(code, family)
        self.mainpage = pywikibot.Page(pywikibot.Link("Main Page", self.mysite))

    def testLoadRevisions_basic(self):
        """Test the site.loadrevisions() method"""

        self.mysite.loadrevisions(self.mainpage, total=15)
        self.assertTrue(hasattr(self.mainpage, "_revid"))
        self.assertTrue(hasattr(self.mainpage, "_revisions"))
        self.assertTrue(self.mainpage._revid in self.mainpage._revisions)
        self.assertEqual(len(self.mainpage._revisions), 15)
        self.assertEqual(self.mainpage._text, None)

    def testLoadRevisions_getText(self):
        """Test the site.loadrevisions() method with getText=True"""

        self.mysite.loadrevisions(self.mainpage, getText=True, total=5)
        self.assertTrue(len(self.mainpage._text) > 0)

    def testLoadRevisions_revids(self):
        """Test the site.loadrevisions() method, listing based on revid."""

        #revids as list of int
        self.mysite.loadrevisions(self.mainpage, revids=[139992, 139993])
        self.assertTrue(all(rev in self.mainpage._revisions for rev in [139992, 139993]))
        #revids as list of str
        self.mysite.loadrevisions(self.mainpage, revids=['139994', '139995'])
        self.assertTrue(all(rev in self.mainpage._revisions for rev in [139994, 139995]))
        #revids as int
        self.mysite.loadrevisions(self.mainpage, revids=140000)
        self.assertTrue(140000 in self.mainpage._revisions)
        #revids as str
        self.mysite.loadrevisions(self.mainpage, revids='140001')
        self.assertTrue(140001 in self.mainpage._revisions)
        #revids belonging to a different page raises Exception
        self.assertRaises(pywikibot.Error, self.mysite.loadrevisions,
                          self.mainpage, revids=130000)

    def testLoadRevisions_querycontinue(self):
        """Test the site.loadrevisions() method with query-continue"""

        self.mysite.loadrevisions(self.mainpage, step=5, total=12)
        self.assertEqual(len(self.mainpage._revisions), 12)

    def testLoadRevisions_revdir(self):
        """Test the site.loadrevisions() method with rvdir=True"""

        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)

    def testLoadRevisions_timestamp(self):
        """Test the site.loadrevisions() method, listing based on timestamp."""

        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)
        revs = self.mainpage._revisions
        timestamps = [str(revs[rev].timestamp) for rev in revs]
        self.assertTrue(all(ts < "2002-01-31T00:00:00Z" for ts in timestamps))

        # Retrieve oldest revisions; listing based on timestamp.
        # Raises "loadrevisions: starttime > endtime with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          starttime="2002-02-01T00:00:00Z", endtime="2002-01-01T00:00:00Z")

        # Retrieve newest revisions; listing based on timestamp.
        # Raises "loadrevisions: endtime > starttime with rvdir=False"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          starttime="2002-01-01T00:00:00Z", endtime="2002-02-01T000:00:00Z")

    def testLoadRevisions_rev_id(self):
        """Test the site.loadrevisions() method, listing based on rev_id."""

        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)
        revs = self.mainpage._revisions
        self.assertTrue(all(139900 <= rev <= 140100 for rev in revs))

        # Retrieve oldest revisions; listing based on revid.
        # Raises "loadrevisions: startid > endid with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          startid="200000", endid="100000")

        # Retrieve newest revisions; listing based on revid.
        # Raises "loadrevisions: endid > startid with rvdir=False
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          startid="100000", endid="200000")

    def testLoadRevisions_user(self):
        """Test the site.loadrevisions() method, filtering by user."""

        # Only list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  user="Magnus Manske")
        revs = self.mainpage._revisions
        self.assertTrue(all(revs[rev].user == "Magnus Manske" for rev in revs))

    def testLoadRevisions_excludeuser(self):
        """Test the site.loadrevisions() method, excluding user."""

        # Do not list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  excludeuser="Magnus Manske")
        revs = self.mainpage._revisions
        self.assertFalse(any(revs[rev].user == "Magnus Manske" for rev in revs))

        # TODO test other optional arguments


class TestMustBe(PywikibotTestCase):
    """Test cases for the must_be decorator."""

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        self._logged_in_as = None

    def login(self, sysop):
        # mock call
        self._logged_in_as = 'sysop' if sysop else 'user'

    def testMockInTest(self):
        self.assertEqual(self._logged_in_as, None)
        self.login(True)
        self.assertEqual(self._logged_in_as, 'sysop')

    testMockInTestReset = testMockInTest

    @must_be('sysop')
    def call_this_sysop_req_function(self, *args, **kwargs):
        return args, kwargs

    @must_be('user')
    def call_this_user_req_function(self, *args, **kwargs):
        return args, kwargs

    def testMustBeSysop(self):
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        retval = self.call_this_sysop_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.assertEqual(self._logged_in_as, 'sysop')

    def testMustBeUser(self):
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        retval = self.call_this_user_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.assertEqual(self._logged_in_as, 'user')

    def testOverrideUserType(self):
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        retval = self.call_this_user_req_function(*args, as_group='sysop', **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.assertEqual(self._logged_in_as, 'sysop')

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
