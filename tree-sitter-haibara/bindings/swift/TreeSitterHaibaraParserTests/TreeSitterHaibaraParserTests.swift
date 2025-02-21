import XCTest
import SwiftTreeSitter
import TreeSitterHaibaraParser

final class TreeSitterHaibaraParserTests: XCTestCase {
    func testCanLoadGrammar() throws {
        let parser = Parser()
        let language = Language(language: tree_sitter_haibara_parser())
        XCTAssertNoThrow(try parser.setLanguage(language),
                         "Error loading HaibaraParser grammar")
    }
}
