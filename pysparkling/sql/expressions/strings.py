from pysparkling.sql.expressions.expressions import UnaryExpression, Expression
from pysparkling.sql.types import StringType


class StringTrim(UnaryExpression):
    def eval(self, row, schema):
        return self.column.eval(row, schema).strip()

    def __str__(self):
        return "trim({0})".format(self.column)


class StringLTrim(UnaryExpression):
    def eval(self, row, schema):
        return self.column.eval(row, schema).lstrip()

    def __str__(self):
        return "ltrim({0})".format(self.column)


class StringRTrim(UnaryExpression):
    def eval(self, row, schema):
        return self.column.eval(row, schema).rstrip()

    def __str__(self):
        return "rtrim({0})".format(self.column)


class StringInStr(Expression):
    def __init__(self, substr, column):
        super(StringInStr, self).__init__(column)
        self.substr = substr
        self.column = column

    def eval(self, row, schema):
        value = self.column.cast(StringType()).eval(row, schema)
        return int(self.substr in value)

    def __str__(self):
        return "instr({0}, {1})".format(
            self.substr,
            self.column
        )


class StringLocate(Expression):
    def __init__(self, substr, column, pos):
        super(StringLocate, self).__init__(column)
        self.substr = substr
        self.column = column
        self.start = pos - 1

    def eval(self, row, schema):
        value = self.column.cast(StringType()).eval(row, schema)
        if self.substr not in value[self.start:]:
            return 0
        return value.index(self.substr, self.start) + 1

    def __str__(self):
        return "locate({0}, {1}{2})".format(
            self.substr,
            self.column,
            ", {0}".format(self.start) if self.start is not None else ""
        )
