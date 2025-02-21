package tree_sitter_haibara_parser_test

import (
	"testing"

	tree_sitter "github.com/tree-sitter/go-tree-sitter"
	tree_sitter_haibara_parser "github.com/heng-zhong-2003/bachelor-thesis-project/bindings/go"
)

func TestCanLoadGrammar(t *testing.T) {
	language := tree_sitter.NewLanguage(tree_sitter_haibara_parser.Language())
	if language == nil {
		t.Errorf("Error loading HaibaraParser grammar")
	}
}
