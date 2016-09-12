import json
import pytest
from decimal import Decimal
from yangson import DataModel
from yangson.context import (Context, FeatureExprParser, BadPath,
                             InvalidFeatureExpression, UnknownPrefix)
from yangson.datatype import YangTypeError
from yangson.enumerations import ContentType
from yangson.instance import (InstanceIdParser, NonexistentInstance,
                              ResourceIdParser)
from yangson.instvalue import ArrayValue, ObjectValue
from yangson.schema import SequenceNode, NonexistentSchemaNode, SchemaError
from yangson.xpathast import XPathTypeError
from yangson.xpathparser import InvalidXPath, NotSupported, XPathParser

tree = """+--rw (test:choiA)?
|  +--:(test:caseA)
|  |  +--rw test:contC
|  |  |  +--rw leafD?
|  |  |  +--rw llistA*
|  |  +--rw test:leafH?
|  +--:(testb:leafQ)
|  |  +--rw testb:leafQ?
|  +--:(test:llistB)
|     +--rw test:llistB*
+--rw test:contA
|  +--rw anydA
|  +--rw anyxA?
|  +--rw (testb:choiB)
|  |  +--:(testb:contB)
|  |  |  +--rw testb:contB!
|  |  |     +--rw leafC
|  |  +--:(testb:leafI)
|  |  |  +--rw testb:leafI?
|  |  +--:(testb:leafN)
|  |     +--rw testb:leafN?
|  +--rw leafA?
|  +--ro leafB
|  +--rw testb:leafR?
|  +--rw testb:leafS?
|  +--rw testb:leafT?
|  +--rw testb:leafV
|  +--rw listA* [leafE leafF]
|     +--rw contD
|     |  +--rw contE!
|     |  |  +--rw leafJ?
|     |  |  +--rw leafP?
|     |  |  +--rw leafU?
|     |  +--rw leafG?
|     |  +--ro leafL
|     +--rw leafE
|     +--rw leafF
+--rw test:contT
|  +--rw binary?
|  +--rw bits?
|  +--rw boolean?
|  +--rw decimal64?
|  +--rw enumeration?
|  +--rw int16?
|  +--rw int32?
|  +--rw int64?
|  +--rw int8?
|  +--rw string?
|  +--rw uint16?
|  +--rw uint32?
|  +--rw uint64?
|  +--rw uint8?
+--ro testb:leafK?
+--rw testb:leafO?
+--ro testb:llistC*
"""

@pytest.fixture
def data_model():
    return DataModel.from_file("examples/test/yang-library-data.json",
                               ["examples/test", "examples/ietf"])

@pytest.fixture
def instance(data_model):
    data = """
    {
        "test:llistB": ["::1", "127.0.0.1"],
	    "test:contA": {
		    "leafB": 9,
		    "listA": [{
			    "leafE": "C0FFEE",
			    "leafF": true,
			    "contD": {
				    "leafG": "foo1-bar",
				    "contE": {
					    "leafJ": [null],
					    "leafP": 10
				    }
			    }
		    }, {
			    "leafE": "ABBA",
			    "leafF": false
		    }],
            "testb:leafS":
                "/test:contA/listA[leafE='C0FFEE'][leafF='true']/contD/contE/leafP",
            "testb:leafR": "C0FFEE",
            "testb:leafT": "test:CC-BY",
            "testb:leafV": 99,
		    "anydA": {
			    "foo:bar": [1, 2, 3]
		    },
		    "testb:leafN": "hi!"
	    },
        "test:contT": {
            "bits": "dos cuatro",
            "decimal64": 4.50,
            "enumeration": "Phobos"
        }
    }
    """
    return data_model.from_raw(json.loads(data))

def test_context(data_model):
    assert len(Context.implement) == 2
    assert data_model.module_set_id() == "b6d7e0614440c5ad8a7370fe46c777254d331983"
    tid = Context.last_revision("test")
    stid = Context.last_revision("subtest")
    tbid = Context.last_revision("testb")
    assert Context.modules[tid].statement.argument == "test"
    assert Context.translate_pname("t:foo", tbid) == ("foo", "test")
    assert Context.translate_pname("sd:foo", stid) == ("foo", "defs")
    with pytest.raises(UnknownPrefix):
        Context.translate_pname("d:foo", stid)
    assert FeatureExprParser("feA and not (not feA or feB)", tid).parse()
    with pytest.raises(InvalidFeatureExpression):
        FeatureExprParser("feA andnot (not feA or feB)", tid).parse()
    assert not Context.is_derived_from(("all-uses", "test"), ("all-uses", "test"))
    assert Context.is_derived_from(("all-uses", "test"), ("licence-property", "test"))
    assert Context.is_derived_from(("CC-BY-SA", "testb"), ("share-alike", "test"))
    assert not Context.is_derived_from(("CC-BY-SA", "testb"), ("derivatives", "test"))
    assert Context.is_derived_from(("CC-BY-SA", "testb"), ("all-uses", "test"))

def test_schema(data_model):
    ca = data_model.get_data_node("/test:contA")
    la = ca.get_child("leafA")
    lsta = data_model.get_data_node("/test:contA/listA")
    ada = ca.get_child("anydA", "test")
    axa = ca.get_child("anyxA", "test")
    cha = data_model.get_schema_node("/test:choiA")
    cc = cha.get_data_child("contC", "test")
    ld = data_model.get_data_node("/test:contC/leafD")
    lla = cc.get_child("llistA", "test")
    chb = data_model.get_schema_node("/test:contA/testb:choiB")
    cb = chb.get_data_child("contB", "testb")
    ln = chb.get_schema_descendant(Context.path2route(
        "/testb:leafN/leafN"))
    lc = cb.get_data_child("leafC", "testb")
    llb = data_model.get_schema_node("/test:choiA/llistB/llistB")
    lj = data_model.get_data_node("/test:contA/listA/contD/contE/leafJ")
    assert data_model.get_data_node("/test:contA/listA/contD/leafM") is None
    llc = data_model.get_schema_node("/testb:rpcA/output/llistC")
    ll = lsta.get_schema_descendant(Context.path2route(
        "test:contD/acA/output/leafL"))
    lo = data_model.get_schema_node("/testb:noA/leafO")
    lp = data_model.get_data_node("/test:contA/listA/contD/contE/leafP")
    assert la.parent == chb.parent == ca
    assert ll.parent.name == "output"
    assert chb in ca._mandatory_children
    assert ada in ca._mandatory_children
    assert (ada.config == axa.config == la.config == ca.config ==
            ld.config == lc.config == lj.config == ln.config == cha.config == True)
    assert ll.config == False
    assert la.ns == ld.ns
    assert lc.ns == "testb"
    assert la.default_value() == 11
    assert ld.default_value() == 199
    assert ld.type.default == 111
    assert lla.default_value() == ArrayValue([42, 54])
    assert lla.type.default == 11
    assert lo.default_value() == True
    assert lp.default_value() == 42
    assert lsta.default_value() == ObjectValue()
    assert la.type.parse_value("99") == 99
    with pytest.raises(YangTypeError):
        ld.type.parse_value("99")
    assert ca.presence == (not cb.presence) == cc.presence == False
    assert llb.min_elements == 2
    assert llb.max_elements == 3
    assert lla.min_elements == llc.min_elements == 0
    assert lla.max_elements is None
    assert llb.user_ordered == (not lla.user_ordered) == True
    assert lsta.get_schema_descendant(lsta.keys[1:]).name == "leafF"
    assert lsta.get_schema_descendant(lsta.unique[0][0]).name == "leafG"
    assert data_model.get_data_node("/test:contA/listA/contD/leafM") is None
    assert data_model.get_data_node("/testb:noA/leafO") is None

def test_tree(data_model):
    assert data_model.ascii_tree() == tree

def test_types(data_model):
    llb = data_model.get_data_node("/test:llistB").type
    assert llb.contains("192.168.1.254")
    assert not llb.contains("300.1.1.1")
    assert not llb.contains("127.0.1")
    with pytest.raises(YangTypeError):
        llb.parse_value("1.2.3.4.5")
    assert llb.contains("2001:db8:0:2::1")
    assert llb.contains("::1")
    assert not llb.contains("2001::db8:0:2::1")
    ct = data_model.get_data_node("/test:contT")
    i8 = ct.get_child("int8", "test").type
    assert i8.contains(100) == (not i8.contains(-101)) == True
    i16 = ct.get_child("int16", "test").type
    assert i16.contains(-32768) == (not i16.contains(32768)) == True
    i32 = ct.get_child("int32", "test").type
    assert i32.contains(-2147483648) == (not i32.contains(2147483648)) == True
    i64 = ct.get_child("int64", "test").type
    assert (i64.contains(-9223372036854775808) ==
            (not i64.contains(9223372036854775808)) == True)
    assert i64.from_raw("-6378") == -6378
    ui8 = ct.get_child("uint8", "test").type
    assert ui8.contains(150) == (not ui8.contains(99)) == True
    ui16 = ct.get_child("uint16", "test").type
    assert ui16.contains(65535) == (not ui16.contains(-1)) == True
    ui32 = ct.get_child("uint32", "test").type
    assert ui32.contains(4294967295) == (not ui32.contains(-1)) == True
    ui64 = ct.get_child("uint64", "test").type
    assert (ui64.contains(18446744073709551615) ==
            (not ui64.contains(-1)) == True)
    assert ui64.from_raw("6378") == 6378
    with pytest.raises(YangTypeError):
        ui64.from_raw("-6378")
    d64 = ct.get_child("decimal64", "test").type
    pi = Decimal("3.141592653589793238")
    assert d64.contains(pi)
    assert not d64.contains(10)
    assert d64.from_raw("3.14159265358979323846264338327950288") == pi
    assert d64.canonical_string(Decimal("0")) == "0.0"
    st = ct.get_child("string", "test").type
    assert st.contains("hello world")
    assert not st.contains("hello-world")
    assert not st.contains("h")
    assert st.contains("9 \tx")
    assert not st.contains("xx xabcdefg")
    boo = ct.get_child("boolean", "test").type
    assert boo.parse_value("true")
    assert boo.contains(False)
    assert boo.canonical_string(True) == "true"
    with pytest.raises(YangTypeError):
        boo.parse_value("boo")
    en = ct.get_child("enumeration", "test").type
    assert not en.contains("Mars")
    assert not en.contains("Deimos")
    assert en.enum["Phobos"] == 101
    bits = ct.get_child("bits", "test").type
    assert bits.as_int(bits._convert_raw("dos cuatro")) == 10
    with pytest.raises(YangTypeError):
        bits.parse_value("un dos")
    assert bits.canonical_string(("cuatro", "dos")) == "dos cuatro"
    with pytest.raises(YangTypeError):
        bits.canonical_string("un dos")
    assert not bits.contains("un")
    assert not bits.contains("tres")
    assert bits.bit["dos"] == 1
    bin = ct.get_child("binary", "test").type
    kun = "Příliš žluťoučký kůň úpěl ďábelské ódy."
    bv = bin.parse_value(
        b'UMWZw61sacWhIMW+bHXFpW91xI1rw70ga8' +
        b'WvxYggw7pwxJtsIMSPw6FiZWxza8OpIMOzZHku')
    assert bv.decode("utf-8") == kun
    assert bin.canonical_string(kun.encode("utf-8")) == (
        "UMWZw61sacWhIMW+bHXFpW91xI1rw70ga8" +
        "WvxYggw7pwxJtsIMSPw6FiZWxza8OpIMOzZHku")

def test_instance(instance):
    def axtest(expr, res):
        assert [ i.json_pointer() for i in expr ] == res
    hi = hash(instance)
    instd = instance.add_defaults()
    hix = hash(instance)
    hid = hash(instd)
    assert hi == hix
    assert hi != hid
    conta = instance.member("test:contA")
    la1 = conta.member("listA").last_entry()
    lt = conta.member("testb:leafT")
    assert la1.index == 1
    tbln = conta.member("testb:leafN")
    inst1 = la1.put_member("leafE", "ABBA").top()
    inst2 = tbln.update("hello!").top()
    assert instance.value == inst1.value
    assert instance.value != inst2.value
    assert instance.timestamp < inst1.timestamp < inst2.timestamp
    assert inst1.json_pointer() == inst2.json_pointer() == "/"
    assert la1.namespace == "test"
    assert la1.member("leafE").namespace == "test"
    assert la1.member("leafF").value is False
    with pytest.raises(NonexistentInstance):
        la1.member("contD")
    assert la1.json_pointer() == "/test:contA/listA/1"
    assert lt.value == ("CC-BY", "test")
    assert str(lt) == "test:CC-BY"
    assert tbln.namespace == "testb"
    assert tbln.json_pointer() == "/test:contA/testb:leafN"
    assert (instance._ancestors() == instance._preceding_siblings() ==
            instance._following_siblings() == [])
    axtest(instance._ancestors_or_self(), ["/"])
    axtest(la1._ancestors(False), ["/test:contA"])
    axtest(la1._ancestors_or_self(("listA", "test")), ["/test:contA/listA/1" ])
    axtest(la1._preceding_siblings(), ["/test:contA/listA/0"])
    axtest(la1._following_siblings(), [])
    assert len(conta._children()) == 10
    axtest(la1._children(("leafF", "test")), ["/test:contA/listA/1/leafF"])
    assert len(instance._descendants(with_self=True)) == 30
    axtest(conta._descendants(("listA", "test")),
           ["/test:contA/listA/0", "/test:contA/listA/1"])
    axtest(tbln._ancestors_or_self(("leafN", "testb")), ["/test:contA/testb:leafN"])

def test_xpath(instance):
    def xptest(expr, res=True, node=instance, module="test"):
        mid = Context.last_revision(module)
        assert XPathParser(expr, mid).parse().evaluate(node) == res
    conta = instance.member("test:contA")
    lr = conta.member("testb:leafR")
    with pytest.raises(InvalidXPath):
        xptest("foo()")
    with pytest.raises(NotSupported):
        xptest("id()")
    xptest("true()")
    xptest("false()", False)
    xptest("1 div 0", float('inf'))
    xptest("-1 div 0", float('-inf'))
    xptest("string(0 div 0)", "NaN")
    xptest("5 mod 2", 1)
    xptest("5 mod -2", 1)
    xptest("- 5 mod 2", -1)
    xptest("- 5 mod - 2", -1)
    xptest("count(t:llistB)", 2)
    xptest("count(*)", 10, conta)
    xptest("count(*[. > 10])", 2, conta)
    xptest("-leafA", -11, conta)
    xptest(" - - leafA", 11, conta)
    xptest("llistB = '::1'")
    xptest("llistB != '::1'")
    xptest("not(llistB = '::1')", False)
    xptest("llistB[position() = 2]", "127.0.0.1")
    xptest("count(child::llistB/following-sibling::*)", 1)
    xptest("leafA > leafB", node=conta)
    xptest("leafA mod leafB", 2, node=conta)
    xptest("listA/contD/contE/leafJ = ''", node=conta)
    xptest("""listA[leafE='C0FFEE' ][ leafF = 'true']
           /contD/contE/leafP = 10""", node=conta)
    xptest("listA/contD/contE/leafP < leafA | leafB", node=conta)
    xptest("listA/contD/contE/leafP > leafA | leafB", node=conta)
    xptest("listA/contD/contE/leafP = leafA | /contA/leafB", False, conta)
    xptest("/t:contA/t:listA[t:leafE = current()]/t:contD/t:leafG = 'foo1-bar'",
           node=lr, module="testb")
    xptest("../leafN = 'hi!'", node=lr, module="testb")
    xptest("local-name()", "")
    xptest("name()", "")
    xptest("local-name(contA)", "contA")
    xptest("name(contA)", "test:contA")
    xptest("local-name()", "leafR", lr)
    xptest("name()", "testb:leafR", lr)
    xptest("name(../t:listA)", "listA", lr, "testb")
    xptest("count(descendant-or-self::*)", 30)
    xptest("count(descendant::leafE)", 2)
    xptest("count(preceding-sibling::*)", 0, lr, "testb")
    xptest("count(following-sibling::*)", 0, lr, "testb")
    xptest("count(descendant-or-self::contA/descendant-or-self::contA)", 1, conta)
    xptest("count(descendant-or-self::contA/descendant::contA)", 0, conta)
    xptest("listA[last()-1]/following-sibling::*/leafE = 'ABBA'", node=conta)
    xptest("count(//contD/parent::*/following-sibling::*/*)", 3)
    xptest("//leafP = 10")
    xptest("""count(listA[leafE = 'C0FFEE' and leafF = true()]//
           leafP/ancestor::node())""", 5, conta)
    xptest("../* > 9", node=lr, module="testb")
    xptest("local-name(ancestor-or-self::contA)", "contA", conta)
    xptest("string(1.0)", "1")
    xptest("string(true())", "true")
    xptest("string(1 = 2)", "false")
    xptest("string(contT/decimal64)", "4.5")
    xptest("string()", "C0FFEE", lr)
    xptest("concat(../t:leafA, 'foo', ., true())", "11fooC0FFEEtrue", lr, "testb")
    with pytest.raises(InvalidXPath):
        xptest("concat()")
    xptest("starts-with(., 'C0F')", True, lr, "testb")
    xptest("starts-with(//listA//leafP, 1)")
    xptest("contains(., '0FF')", True, lr, "testb")
    xptest("not(contains(../leafN, '!!'))", True, lr, "testb")
    xptest("substring-before(//decimal64, '.')", "4")
    xptest("substring-after(//decimal64, '.')", "5")
    xptest("substring('12345', 1.5, 2.6)", "234")
    xptest("substring('12345', 0, 3)", "12")
    xptest("substring('12345', 0 div 0, 3)", "")
    xptest("substring('12345', 1, 0 div 0)", "")
    xptest("substring('12345', -42, 1 div 0)", "12345")
    xptest("substring('12345', -1 div 0, 1 div 0)", "")
    xptest("substring('12345', -1 div 0)", "12345")
    xptest("substring(//listA[last()]/leafE, 3)", "BA")
    xptest("string-length(llistB)", 3)
    xptest("string-length() = 6", node=lr)
    xptest("""normalize-space('  \tfoo   bar
           baz    ')""", "foo bar baz")
    xptest("translate(., 'ABCDEF', 'abcdef')", "c0ffee", lr)
    xptest("translate('--abcd--', 'abc-', 'ABC')", "ABCd")
    xptest("boolean(foo)", False)
    xptest("boolean(descendant::leafE)")
    xptest("boolean(10 mod 2)", False)
    xptest("boolean(string(llistB))")
    xptest("number(leafA)", 11, conta)
    xptest("string(number())", "NaN", lr, "testb")
    xptest("string(number('foo'))", "NaN")
    xptest("number(true()) = 1")
    xptest("number(false()) = 0")
    xptest("sum(leafA | leafB)", 20, conta)
    xptest("string(sum(//leafE))", "NaN")
    xptest("sum(//leafF)", 1)
    with pytest.raises(XPathTypeError):
        xptest("sum(42)")
    xptest("floor(contT/decimal64)", 4)
    xptest("ceiling(contT/decimal64)", 5)
    xptest("round(contT/decimal64)", 5)
    xptest("round(- 6.5)", -6)
    xptest("round(1 div 0)", float("inf"))
    xptest("round(-1 div 0)", float("-inf"))
    xptest("string(round(0 div 0))", "NaN")
    xptest("re-match(//leafE, '[0-9a-fA-F]*')")
    xptest("re-match(count(//leafE), '[0-9]*')")
    xptest("re-match('1.22.333', '\d{1,3}\.\d{1,3}\.\d{1,3}')")
    xptest("re-match('aaax', 'a*')", False)
    xptest("re-match('a\nb', '.*')", False)
    xptest("re-match('a\nb', '[a-z\n]*')")
    xptest("deref(.)/../t:leafF", True, lr, "testb")
    xptest("deref(../leafS)", 10, lr, "testb")
    xptest("count(deref(../leafS) | ../leafN)", 2, lr, "testb")
    xptest("derived-from-or-self(../leafT, 't:CC-BY')", True, lr, "testb")
    xptest("derived-from(../leafT, 't:CC-BY')", False, lr, "testb")
    xptest("derived-from(../leafT, 't:derivatives')", True, lr, "testb")
    xptest("derived-from(../leafT, 't:share-alike')", False, lr, "testb")
    xptest("derived-from(../leafT, 't:licence-property')", True, lr, "testb")
    xptest("derived-from(., 't:CC-BY')", False, lr, "testb")
    xptest("derived-from(., 'CC-BY')", False, conta)
    xptest("enum-value(//enumeration)", 101)
    xptest("string(enum-value(foo))", "NaN")
    xptest("string(enum-value(.))", "NaN", conta)
    xptest("string(enum-value(.))", "NaN", lr, "testb")
    xptest("bit-is-set(//bits, 'dos') and bit-is-set(//bits, 'cuatro')")
    xptest("not(bit-is-set(foo, bar))")
    xptest("bit-is-set(., 'dos')", False, conta)

def test_instance_paths(data_model, instance):
    rid1 = ResourceIdParser("/test:contA/testb:leafN").parse()
    rid2 = ResourceIdParser(
        "/test:contA/listA=C0FFEE,true/contD/contE").parse()
    iid1 = InstanceIdParser("/test:contA/testb:leafN").parse()
    iid2 = InstanceIdParser(
        "/test:contA/listA[leafE='C0FFEE'][leafF = 'true']/contD/contE").parse()
    iid3 = InstanceIdParser("/test:contA/listA[1]/contD/contE").parse()
    bad_pth = "/test:contA/listA=ABBA,true/contD/contE"
    assert instance.peek(rid1) == instance.peek(iid1) == "hi!"
    assert (instance.goto(rid2).member("leafP").value ==
            instance.goto(iid2).member("leafP").value ==
            instance.goto(iid3).member("leafP").value == 10)
    with pytest.raises(NonexistentSchemaNode):
        ResourceIdParser("/test:contA/leafX").parse()
    with pytest.raises(NonexistentSchemaNode):
        InstanceIdParser("/test:contA/llX[. = 'foo']").parse()
    assert instance.peek(ResourceIdParser(bad_pth).parse()) == None
    with pytest.raises(NonexistentInstance):
        instance.goto(ResourceIdParser(bad_pth).parse())

def test_edits(data_model, instance):
    laii = InstanceIdParser("/test:contA/listA").parse()
    la = instance.goto(laii)
    inst1 = la.entry(1).update(
        {"leafE": "B00F", "leafF": False}, raw=True).top()
    assert instance.peek(laii)[1]["leafE"] == "ABBA"
    assert inst1.peek(laii)[1]["leafE"] == "B00F"
    modla = la.delete_entry(1)
    assert len(modla.value) == 1
    llb1 = instance.member("test:llistB").entry(1)
    modllb = llb1.update("2001:db8:0:2::1", raw=True).up()
    assert modllb.value == ArrayValue(["::1", "2001:db8:0:2::1"])
    with pytest.raises(YangTypeError):
        llb1.update("2001::2::1", raw=True)

def test_validation(instance):
    assert instance.validate(ContentType.all) is None
    inst2 = instance.put_member("testb:leafQ", "ABBA").top()
    with pytest.raises(SchemaError):
        inst2.validate(ContentType.all)
