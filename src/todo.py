def setup(app):
    '''
    新しい要素は、拡張の中のsetup関数の中で追加していきます
    http://www.sphinx-doc.org/ja/master/extdev/appapi.html
    にあるセットアップ関数を使うようだ
    '''

    ''' conf.pyに追加する設定
    :param name: 設定名
    :param default: デフォルトの値
    :param rebuild: リビルド対象となるビルダー名(空文字可)
    '''
    app.add_config_value('todo_include_todos', False, 'html')

    ''' ビルドシステムに対する新規ノード作成
    '''
    app.add_node(todolist)
    app.add_node(todo,
                 html=(visit_todo_node, depart_todo_node),
                 latex=(visit_todo_node, depart_todo_node),
                 text=(visit_todo_node, depart_todo_node))

    ''' ノードに対して実行されるディレクティブを設定
    '''
    app.add_directive('todo', TodoDirective)
    app.add_directive('todolist', TodolistDirective)

    ''' イベントに対するハンドラの追加
    '''
    app.connect('doctree-resolved', process_todo_nodes)
    app.connect('env-purge-doc', purge_todos)

    return {'version': '0.1'}   # identifies the version of our extension
