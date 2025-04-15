            # {% recursetree categories %}
            #     <li class="list-group-item">
            #         <a href="{{ node.get_absolute_url }}">{{ node.name }}</a>
            #         {% if not node.is_leaf_node %}
            #             <ul class="list-group">
            #                 {{ children }}
            #             </ul>
            #         {% endif %}
            #     </li>
            # {% endrecursetree %}