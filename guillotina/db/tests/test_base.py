
from guillotina.db.orm.base import BaseObject
from guillotina.db.orm.interfaces import IAnnotation
from guillotina.db.transaction import Transaction


class TestObject(BaseObject):
    pass


async def test_create_object(dummy_txn_root):
    async for root in dummy_txn_root:
        assert isinstance(root._p_jar, Transaction)
        import pdb; pdb.set_trace()
        ob1 = TestObject()
        assert ob1._p_jar is None
        assert ob1._p_serial is None
        assert ob1._p_oid is None
        assert ob1.__parent__ is None

        await root.__setitem__('ob1', ob1)

        assert ob1._p_jar == root._p_jar
        assert ob1._p_serial is not None
        assert ob1._p_oid is not None
        assert ob1.__parent__ is root


async def test_create_subobject(dummy_root):
    async for root in dummy_root:
        import pdb; pdb.set_trace()
    import pdb; pdb.set_trace()
    ob1 = TestObject()
    assert ob1._p_jar is None
    assert ob1._p_serial is None
    ob2 = TestObject()
    ob1.attribute = ob2
    assert ob2._p_belongs == ob1._p_oid == None

    import pdb; pdb.set_trace()


def test_create_annotation(guillotina_main):
    ob1 = TestObject()
    assert ob1._p_jar is None
    assert ob1._p_serial is None
    annotation = IAnnotation(ob1)
    annotation._p_belongs == ob1._p_oid
