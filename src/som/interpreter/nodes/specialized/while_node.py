from ..expression_node import ExpressionNode
from rpython.rlib import jit
from som.vmobjects.method import Method


class AbstractWhileMessageNode(ExpressionNode):

    _immutable_fields_ = ['_predicate_bool', '_rcvr_expr?', '_body_expr?',
                          '_universe']
    _child_nodes_      = ['_rcvr_expr', '_body_expr']

    def __init__(self, rcvr_expr, body_expr, predicate_bool_obj, universe,
                 source_section):
        ExpressionNode.__init__(self, source_section)
        self._predicate_bool = predicate_bool_obj
        self._rcvr_expr      = self.adopt_child(rcvr_expr)
        self._body_expr      = self.adopt_child(body_expr)
        self._universe       = universe

    def execute(self, frame):
        self.execute_void(frame)
        return self._universe.nilObject

    def execute_void(self, frame):
        rcvr_value = self._rcvr_expr.execute(frame)
        body_block = self._body_expr.execute(frame)

        self._do_while(frame, rcvr_value, body_block)

# STEFAN: SOM doesn't actually have #whileTrue:, #whileFalse: for booleans.

# def get_printable_location_while_value(body_method, node):
#     assert isinstance(body_method, Method)
#     return "while_value: %s" % body_method.merge_point_string()
#
# while_value_driver = jit.JitDriver(
#     greens=['body_method', 'node'], reds='auto',
#     get_printable_location = get_printable_location_while_value)
#
#
# class WhileWithValueReceiver(AbstractWhileMessageNode):
#
#     def execute_evaluated(self, frame, rcvr_value, body_block):
#         if rcvr_value is not self._predicate_bool:
#             return self._universe.nilObject
#         body_method = body_block.get_method()
#
#         while True:
#             while_value_driver.jit_merge_point(body_method = body_method,
#                                                node        = self)
#             body_method.invoke(frame, body_block, None)


def get_printable_location_while(body_method, condition_method, while_type):
    assert isinstance(condition_method, Method)
    assert isinstance(body_method, Method)

    return "%s while %s: %s" % (condition_method.merge_point_string(),
                                while_type,
                                body_method.merge_point_string())


while_driver = jit.JitDriver(
    greens=['body_method', 'condition_method', 'node'], reds='auto',
    get_printable_location = get_printable_location_while)


class WhileMessageNode(AbstractWhileMessageNode):

    def execute_evaluated(self, frame, rcvr, args):
        self.execute_evaluated_void(frame, rcvr, args)
        return self._universe.nilObject

    def execute_evaluated_void(self, frame, rcvr, args):
        self._do_while(frame, rcvr, args[0])

    def _do_while(self, frame, rcvr_block, body_block):
        condition_method = rcvr_block.get_method()
        body_method      = body_block.get_method()

        while True:
            while_driver.jit_merge_point(body_method     = body_method,
                                         condition_method= condition_method,
                                         node            = self)

            condition_value = condition_method.invoke(frame, rcvr_block, None)
            if condition_value is not self._predicate_bool:
                break
            body_method.invoke_void(frame, body_block, None)