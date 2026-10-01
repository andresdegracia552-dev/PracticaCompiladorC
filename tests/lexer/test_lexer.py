"""Pruebas del analizador léxico de Mini C.

Verifica categorías de tokens, posiciones (línea y columna), máxima coincidencia,
palabras reservadas frente a identificadores, recuperación con LEX001, EOF único
y los casos de prueba de la especificación.
"""

from minic.lexer import Lexer, Token, TokenType
from minic.output import format_diagnostic, format_token


def test_specification_case_1() -> None:
    source = "int2 = 12abc;\nwhilex == -5"
    lexer = Lexer(source)
    tokens, diagnostics = lexer.scan()

    assert diagnostics == []

    expected_output = [
        "IDENTIFIER 'int2' 1 1",
        "ASSIGN '=' 1 6",
        "INTEGER_LITERAL '12' 1 8",
        "IDENTIFIER 'abc' 1 10",
        "SEMICOLON ';' 1 13",
        "IDENTIFIER 'whilex' 2 1",
        "EQUAL_EQUAL '==' 2 8",
        "MINUS '-' 2 11",
        "INTEGER_LITERAL '5' 2 12",
        "EOF '' 2 13",
    ]

    actual_output = [format_token(t) for t in tokens]
    assert actual_output == expected_output

    # Verificar literales enteros
    assert tokens[2].literal == 12
    assert tokens[8].literal == 5


def test_specification_case_2_with_errors() -> None:
    source = "int x = @;\nx ! = 0; // fin"
    lexer = Lexer(source)
    tokens, diagnostics = lexer.scan()

    expected_tokens = [
        "KW_INT 'int' 1 1",
        "IDENTIFIER 'x' 1 5",
        "ASSIGN '=' 1 7",
        "SEMICOLON ';' 1 10",
        "IDENTIFIER 'x' 2 1",
        "ASSIGN '=' 2 5",
        "INTEGER_LITERAL '0' 2 7",
        "SEMICOLON ';' 2 8",
        "IDENTIFIER 'fin' 2 13",
        "EOF '' 2 16",
    ]

    expected_diagnostics = [
        "LEX001 error 1:9 Carácter no reconocido: '@'",
        "LEX001 error 2:3 Carácter no reconocido: '!'",
        "LEX001 error 2:10 Carácter no reconocido: '/'",
        "LEX001 error 2:11 Carácter no reconocido: '/'",
    ]

    assert [format_token(t) for t in tokens] == expected_tokens
    assert [format_diagnostic(d) for d in diagnostics] == expected_diagnostics


def test_all_single_and_double_operators() -> None:
    source = "= == != + - ( ) { } ;"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    expected_types = [
        TokenType.ASSIGN,
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types


def test_keywords_vs_identifiers() -> None:
    source = "int integer while while_1 _int _while"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert tokens[0].type == TokenType.KW_INT
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[2].type == TokenType.KW_WHILE
    assert tokens[3].type == TokenType.IDENTIFIER
    assert tokens[4].type == TokenType.IDENTIFIER
    assert tokens[5].type == TokenType.IDENTIFIER


def test_number_followed_by_letters() -> None:
    source = "123abc456"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert len(tokens) == 3  # 123, abc456, EOF
    assert tokens[0].type == TokenType.INTEGER_LITERAL
    assert tokens[0].lexeme == "123"
    assert tokens[0].literal == 123
    assert tokens[1].type == TokenType.IDENTIFIER
    assert tokens[1].lexeme == "abc456"
    assert tokens[2].type == TokenType.EOF


def test_integer_literal_leading_zeros() -> None:
    source = "007"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert tokens[0].literal == 7
    assert tokens[0].lexeme == "007"


def test_whitespace_and_positions() -> None:
    # \t cuenta como 1 columna, \r suelto es blanco de 1 col, solo \n abre línea
    source = "a\tb\rc\nd"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    # a: col 1; \t: col 2; b: col 3; \r: col 4; c: col 5
    assert (tokens[0].lexeme, tokens[0].line, tokens[0].column) == ("a", 1, 1)
    assert (tokens[1].lexeme, tokens[1].line, tokens[1].column) == ("b", 1, 3)
    assert (tokens[2].lexeme, tokens[2].line, tokens[2].column) == ("c", 1, 5)
    # \n reinicia a línea 2, columna 1
    assert (tokens[3].lexeme, tokens[3].line, tokens[3].column) == ("d", 2, 1)
    # EOF al final de 'd' -> línea 2, columna 2
    assert (tokens[4].type, tokens[4].line, tokens[4].column) == (TokenType.EOF, 2, 2)


def test_empty_source() -> None:
    tokens, diagnostics = Lexer("").scan()
    assert diagnostics == []
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF
    assert tokens[0].lexeme == ""
    assert tokens[0].literal is None
    assert tokens[0].line == 1
    assert tokens[0].column == 1


def test_unrecognized_characters_recovery() -> None:
    source = "$#?~"
    tokens, diagnostics = Lexer(source).scan()

    assert len(diagnostics) == 4
    assert [d.code for d in diagnostics] == ["LEX001"] * 4
    assert [d.column for d in diagnostics] == [1, 2, 3, 4]
    # Aun con errores se emite el EOF
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF
