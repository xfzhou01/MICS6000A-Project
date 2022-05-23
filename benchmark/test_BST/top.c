void top(int data[10], int L_idx[10], int R_idx[10], int arr_len, int add_data) {
        int size = arr_len;
        int pre_node = -1;
        int cur_node = 0;

        while (cur_node != -1){
                pre_node = cur_node;
                if (add_data < data[cur_node]){
                        cur_node = L_idx[cur_node];
                }else{
                        cur_node = R_idx[cur_node];
                }
        }

        if (add_data < data[pre_node]){
                L_idx[pre_node] = size;
        }else{
                R_idx[pre_node] = size;
        }

        data[size] = add_data;
        L_idx[size] = -1;
        R_idx[size] = -1;

        // Should balance the BST here. But we ignore it.
}