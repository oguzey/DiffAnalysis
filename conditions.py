from enum import Enum
from variable import Variable
from side import Side
from side import SideException


class ConditionExeption(Exception):
    pass


class StateConditions(Enum):
    IS_ZERO = 0
    IS_NOT_ZERO = 1
    IS_EQUAL = 2
    IS_SUMM = 3


class Condition(object):
    """ class describe conditions for system of transitions"""
    def __init__(self, left_side, right_side, state):
        """

        left_side - is list of Variables
        left_side - is list of Variables or None if state eqaul
                        to StateConditions.IS_ZERO
        state - state of condition

        """
        super(Condition, self).__init__()
        is_not_sum = (
            state == StateConditions.IS_ZERO
        )
        if len(right_side) > 0 and is_not_sum:
            raise Exception("Bad values in arguments: "
                            "right_side is %s and state %s" %
                            (right_side, state))
        assert isinstance(left_side, Side) and isinstance(right_side, Side)
        self.__state = state
        self.__left_side = left_side
        self.__right_side = right_side

    def __eq__(self, other):
        assert isinstance(other, Condition)
        return self.__state == other.__state and (
            self.__left_side == other.__left_side and (
                self.__right_side == other.__right_side))

    def __str__(self):
        if self.__state == StateConditions.IS_ZERO:
            assert len(self.__right_side) == 0
            return str(self.__left_side) + " = 0"
        elif self.__state == StateConditions.IS_NOT_ZERO:
            rs = "0" if len(self.__right_side) == 0 else str(self.__right_side)
            return "%s != %s " % (str(self.__left_side), rs)
        else:
            return str(self.__left_side) + " = " + str(self.__right_side)

    def check_condition(self):
        if len(self.__left_side) == 0 and len(self.__right_side) == 0 and (
                self.__state == StateConditions.IS_NOT_ZERO):
            raise ConditionExeption("Bad condition")

    def swap_sides(self):
        print "[swap_sides] ", str(self)
        # assert len(self.__left_side) == 0 and len(self.__right_side) > 0
        right = self.__right_side
        self.__right_side = self.__left_side
        self.__left_side = right

    def get_left_side(self):
        return self.__left_side

    def get_right_side(self):
        return self.__right_side

    def get_state(self):
        return self.__state

    def set_state(self, state):
        self.__state = state

    def is_contradiction(self, other):
        assert isinstance(other, Condition)
        if self.__left_side == other.__left_side:
            sum_state = self.__state.value + other.__state.value
            # sum of state IS_ZERO and IS_NOT_ZERO = 1
            if sum_state == 1:
                return True
        return False

    def copy(self):
        return Condition(self.__left_side.copy(), self.__right_side.copy(), self.__state)

    @staticmethod
    def create_zero_condition(side):
        assert isinstance(side, Side) and len(side) > 0
        if len(side) == 1:
            return Condition(side, Side(), StateConditions.IS_ZERO)

        state = StateConditions.IS_EQUAL
        try:
            lat_unknown = side.find_the_latest_unknown()
            side.pop_variable(lat_unknown)
            return Condition(Side(lat_unknown), side, state)
        except SideException:
            try:
                lat_output = side.find_the_latest_output()
                side.pop_variable(lat_output)
                return Condition(Side(lat_output), side, state)
            except SideException:
                lat_input = side.find_the_latest_input()
                side.pop_variable(lat_input)
                return Condition(Side(lat_input), side, state)

    @staticmethod
    def create_non_zero_condition(side):
        assert isinstance(side, Side) and len(side) > 0
        return Condition(side, Side(), StateConditions.IS_NOT_ZERO)


class CommonCondition(object):
    def __init__(self, zero_cond, non_zero_cond):
        assert isinstance(zero_cond, list) and isinstance(non_zero_cond, list)
        self.__zero_cond = zero_cond
        self.__non_zero_cond = non_zero_cond

    def __str__(self):
        z_str = "; ".join(map(str, self.__zero_cond))
        nz_str = "; ".join(map(str, self.__non_zero_cond))
        str_cc = "{\n\tZero condition: %s" % z_str
        str_cc += "\n\tNon zero condition: %s\n}" % nz_str
        return str_cc

    def append_zero_condition(self, condition):
        assert condition.get_state() == StateConditions.IS_ZERO and (
            len(condition.get_right_side()) == 0)
        self.__zero_cond.append(condition)

    def append_non_zero_condition(self, condition):
        assert condition.get_state() == StateConditions.IS_NOT_ZERO and (
            len(condition.get_right_side()) == 0)
        self.__non_zero_cond.append(condition)

    def get_zero_condition(self):
        return tuple(self.__zero_cond)

    def get_non_zero_condition(self):
        return tuple(self.__non_zero_cond)


class CommonConditions(object):
    """ condition for input and output variables """
    def __init__(self, *input_variables):
        assert all([isinstance(x, Variable) and not x.is_unknown()
                    for x in input_variables])
        self.__input_variables = input_variables
        self.__conditions = []

    def __len__(self):
        return len(self.__conditions)

    @staticmethod
    def get_num_bits(number, max_bits):
        res = []
        counter = 0
        comp = 1
        while counter < max_bits:
            if (comp & number) > 0:
                res.append(counter)
            counter += 1
            comp *= 2
        return res

    @staticmethod
    def comparator(lst1, lst2):
        if len(lst1) < len(lst2):
            return -1
        elif len(lst1) > len(lst2):
            return 1
        else:
            return 1 if lst1 > lst2 else -1

    def generate_conditions(self):
        if len(self.__conditions) > 0:
            return self.__conditions

        max_bits = len(self.__input_variables)
        max_number = pow(2, max_bits)

        all_zero_pos = []

        for x in xrange(1, max_number - 1):
            all_zero_pos.append(self.get_num_bits(x, max_bits))
        all_zero_pos.sort(self.comparator)
        all_zero_pos.append([])

        for zero_pos in all_zero_pos:
            zero_vars = []
            none_zero_vars = []
            for ind in xrange(len(self.__input_variables)):
                if ind in zero_pos:
                    zero_vars.append(Condition(
                        Side(self.__input_variables[ind]),
                        Side(),
                        StateConditions.IS_ZERO)
                    )
                else:
                    none_zero_vars.append(Condition(
                        Side(self.__input_variables[ind]),
                        Side(),
                        StateConditions.IS_NOT_ZERO))
            self.__conditions.append(CommonCondition(zero_vars, none_zero_vars))
        return "OK"

    def get_condition(self, index):
        if index > len(self) - 1 or index < 0:
            raise Exception("Wrong index")
        return self.__conditions[index]


class CustomConditions(object):
    """
    conditions which is created during applying CommonConditions and assumption
    """
    def __init__(self):
        self.__conditions = []

    def __str__(self):
        str_cc = "\n\t".join(map(str, self.__conditions))
        return "{ \n\t" + str_cc + " \n}"

    def __len__(self):
        return len(self.__conditions)

    def append_condition(self, condition):
        # print "append cond = ", str(condition)
        left_side = condition.get_left_side()
        right_side = condition.get_right_side()
        # assert len(left_side) == 1
        # print "!!!before cond { "+"\n".join(map(str, self.__conditions))+"\n}"

        for cond in self.__conditions:
            if cond.get_right_side() == right_side and (
                cond.get_left_side() == left_side and (
                    cond.get_state() == condition.get_state())):
                print "Find the same condition %s" % str(condition)
                return

        if condition.get_state() == StateConditions.IS_NOT_ZERO:
            self.__conditions.append(condition)
            self.__update_conditions()
            return

        for cond in self.__conditions:
            right = cond.get_right_side()
            left = cond.get_left_side()
            if right.contains(left_side):
                right.replace_in_side(left_side, right_side)
                if len(right) == 0 and cond.get_state() != StateConditions.IS_NOT_ZERO:
                    cond.set_state(StateConditions.IS_ZERO)
            if left.contains(left_side):
                left.replace_in_side(left_side, right_side)
                if len(left) == 0:
                    cond.swap_sides()
                    if cond.get_state() != StateConditions.IS_NOT_ZERO:
                        cond.set_state(StateConditions.IS_ZERO)
            cond.check_condition()
        self.__conditions.append(condition)

        self.__update_conditions()

    def __update_conditions(self):
        for cond1 in self.__conditions:
            if cond1.get_state() == StateConditions.IS_NOT_ZERO:
                continue
            left1 = cond1.get_left_side()
            for cond2 in self.__conditions:
                if cond1 == cond2:
                    continue
                right2 = cond2.get_right_side()
                left2 = cond2.get_left_side()
                if right2.contains(left1):
                    right2.replace_in_side(left1, cond1.get_right_side())

                    if len(right2) == 0 and (
                            cond2.get_state() != StateConditions.IS_NOT_ZERO):
                        cond2.set_state(StateConditions.IS_ZERO)
                if left2.contains(left1):
                    left2.replace_in_side(left1, cond1.get_right_side())
                    if len(left2) == 0:
                        cond2.swap_sides()
                        if cond2.get_state() != StateConditions.IS_NOT_ZERO:
                            cond2.set_state(StateConditions.IS_ZERO)
                cond2.check_condition()

    def get_condition(self, index):
        assert index <= len(self.__conditions)
        return self.__conditions[index]

    def exist_contradiction(self, *common_conditions):
        for com_cond in common_conditions:
            assert isinstance(com_cond, CommonCondition)

            nz_z_c = list(com_cond.get_non_zero_condition())
            nz_z_c.extend(com_cond.get_zero_condition())

            for self_cond in self.__conditions:
                for c in nz_z_c:
                    if c.is_contradiction(self_cond):
                        return True
        return False

    def copy(self):
        new_cc = CustomConditions()
        for condition in self.__conditions:
            new_cc.append_condition(condition.copy())

        # print "\n\n--------start copy custom condition --------"
        # print "old system %s" % str(self)
        # print "new system %s" % str(new_cc)
        # print "--------end copy custom condition --------\n\n"

        return new_cc

    def is_side_non_zero(self, side, common_in, common_out):
        nz_c = list(common_in.get_non_zero_condition())
        nz_c.extend(common_out.get_non_zero_condition())
        nz_sides = [cond.get_left_side() for cond in nz_c]

        if side in nz_sides:
            return True

        for condition in self.__conditions:
            left = condition.get_left_side()
            assert len(left) > 0
            if condition.get_state() == StateConditions.IS_NOT_ZERO and left == side:
                return True
        return False
