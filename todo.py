"""
===================
TODO 拡張機能
===================

`Sphinxチュートリアル <http://www.sphinx-doc.org/ja/master/extdev/tutorial.html>`_ より

"""

from docutils import nodes  # ノードクラスを作るために必要
from docutils.parsers.rst import Directive # ディレクティブクラスを作るために必要
from sphinx.locale import _


def setup(app):
    """
    新しい要素は、拡張の中のsetup関数の中で追加していきます
    http://www.sphinx-doc.org/ja/master/extdev/appapi.html
    にあるセットアップ関数を使うようだ
    """

    """
    conf.pyに追加する設定
    ------------------------
    :param name: 設定名
    :param default: デフォルトの値
    :param rebuild: リビルド対象となるビルダー名(空文字可)
    """
    app.add_config_value('todo_include_todos', False, 'html')

    """
    ビルドシステムに対する新規ノード作成
    -------------------------------------
    ``.. image::``のようなノードを宣言します
    ここでは、 .. todolist:: と .. todo:: が存在するよーと言っている
    """
    app.add_node(todolist)
    app.add_node(todo,
                 html=(visit_todo_node, depart_todo_node),
                 latex=(visit_todo_node, depart_todo_node),
                 text=(visit_todo_node, depart_todo_node))

    """
    ノードに対して実行されるディレクティブを設定
    ---------------------------------------------
    各ノードの実装を設定します。
    todo なら TodoDirective というクラスが、ソースを解釈します
    """
    app.add_directive('todo', TodoDirective)
    app.add_directive('todolist', TodolistDirective)

    """ イベントに対するハンドラの追加
    """
    app.connect('doctree-resolved', process_todo_nodes)
    app.connect('env-purge-doc', purge_todos)

    return {'version': '0.1'}   # identifies the version of our extension



#####################################################################
# ノードクラス
#####################################################################
class todo(nodes.Admonition, nodes.Element):
    """
    .. todo::
    """
    pass

class todolist(nodes.General, nodes.Element):
    """
    .. todolist::
    """
    pass

def visit_todo_node(self, node):
    self.visit_admonition(node)

def depart_todo_node(self, node):
    self.depart_admonition(node)



#####################################################################
# ディレクティブクラス
#####################################################################
class TodolistDirective(Directive):
    """
    todolistディレクティブ
    """

    def run(self):
        """
        :return: todolistノードクラスのインスタンス
        """
        return [todolist('')]



class TodoDirective(Directive):
    """
    todoディレクティブ
    """

    # これにより、ディレクティブの内容が有効になります
    has_content = True

    def run(self):
        env = self.state.document.settings.env  # ビルド環境のインスタンスを参照

        # ターゲットノードの抽出
        targetid = "todo-%d" % env.new_serialno('todo') # リンクターゲットの為のユニーク名
        targetnode = nodes.target('', '', ids=[targetid]) # リンクターゲットを抽出

        # admonitionノード(todoノード)の抽出
        todo_node = todo('\n'.join(self.content))   # todoノード作成
        todo_node += nodes.title(_('Todo'), _('Todo'))  # todoノードにタイトルを追加
        self.state.nested_parse(self.content, self.content_offset, todo_node) # ソース本体をパース

        # 作成したtodoノードを、todolistディレクティブに追加
        if not hasattr(env, 'todo_all_todos'):
            env.todo_all_todos = []
        env.todo_all_todos.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'todo': todo_node.deepcopy(),
            'target': targetnode,
        })

        # todoノードをDOCツリーに配置
        return [targetnode, todo_node]



#####################################################################
# イベントハンドラ
#####################################################################
def purge_todos(app, env, docname):
    """
    ソースファイルが削除されたなどのイベント時に呼ばれます
    データを一旦クリアにします
    """
    if not hasattr(env, 'todo_all_todos'):
        return
    env.todo_all_todos = [todo for todo in env.todo_all_todos
                          if todo['docname'] != docname]



def process_todo_nodes(app, doctree, fromdocname):
    """
    doctreeが解決されたとき(すべての参照が解決されたとき)に呼ばれます
    """

    # "todo_include_todos"設定がFalseの場合、
    # todo,todolistのノードすべてがソースから削除されます
    if not app.config.todo_include_todos:
        for node in doctree.traverse(todo):
            node.parent.remove(node)

    # 全てのtodolistノードを、収集されたtodosの配列に置き換えます
    # オリジナルの位置へのリンクを付けて、各todoを拡張します
    env = app.builder.env

    for node in doctree.traverse(todolist):
        if not app.config.todo_include_todos:
            node.replace_self([])
            continue

        content = []

        # 削除されなかったtodoは、どこにどのように存在するのかだけを維持します
        for todo_info in env.todo_all_todos:
            para = nodes.paragraph()
            filename = env.doc2path(todo_info['docname'], base=None)
            description = (
                _('(The original entry is located in %s, line %d and can be found ') %
                (filename, todo_info['lineno']))
            para += nodes.Text(description, description)

            # 新規ノードを作成します
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_('here'), _('here'))
            newnode['refdocname'] = todo_info['docname']
            newnode['refuri'] = app.builder.get_relative_uri(
                fromdocname, todo_info['docname'])
            newnode['refuri'] += '#' + todo_info['target']['refid']
            newnode.append(innernode)
            para += newnode
            para += nodes.Text('.)', '.)')

            # todolistを挿入します
            content.append(todo_info['todo'])
            content.append(para)
        
        node.replace_self(content)
