#include <iostream>
#include <vector>

using namespace std;

// Matrix addition for Strassen logic
vector<vector<int>> add(vector<vector<int>> A, vector<vector<int>> B, int n) {
	vector<vector<int>> res(n, vector<int>(n));
	for (int i = 0; i < n; i++)
		for (int j = 0; j < n; j++)
			res[i][j] = A[i][j] + B[i][j];
	return res;
}

// Matrix subtraction for Strassen logic
vector<vector<int>> sub(vector<vector<int>> A, vector<vector<int>> B, int n) {
	vector<vector<int>> res(n, vector<int>(n));
	for (int i = 0; i < n; i++)
		for (int j = 0; j < n; j++)
			res[i][j] = A[i][j] - B[i][j];
	return res;
}

// The core: Strassen's recursive multiplication
vector<vector<int>> strassen(vector<vector<int>> A, vector<vector<int>> B, int n) {
	if (n == 1) {
		return { {A[0][0] * B[0][0]} };
	}

	int new_n = n / 2;
	vector<int> row(new_n, 0);
	vector<vector<int>> a11(new_n, row), a12(new_n, row), a21(new_n, row), a22(new_n, row);
	vector<vector<int>> b11(new_n, row), b12(new_n, row), b21(new_n, row), b22(new_n, row);

	// Splitting matrices into quadrants
	for (int i = 0; i < new_n; i++) {
		for (int j = 0; j < new_n; j++) {
			a11[i][j] = A[i][j];
			a12[i][j] = A[i][j + new_n];
			a21[i][j] = A[i + new_n][j];
			a22[i][j] = A[i + new_n][j + new_n];

			b11[i][j] = B[i][j];
			b12[i][j] = B[i][j + new_n];
			b21[i][j] = B[i + new_n][j];
			b22[i][j] = B[i + new_n][j + new_n];
		}
	}

	// Strassen's 7 products
	auto p1 = strassen(add(a11, a22, new_n), add(b11, b22, new_n), new_n);
	auto p2 = strassen(add(a21, a22, new_n), b11, new_n);
	auto p3 = strassen(a11, sub(b12, b22, new_n), new_n);
	auto p4 = strassen(a22, sub(b21, b11, new_n), new_n);
	auto p5 = strassen(add(a11, a12, new_n), b22, new_n);
	auto p6 = strassen(sub(a21, a11, new_n), add(b11, b12, new_n), new_n);
	auto p7 = strassen(sub(a12, a22, new_n), add(b21, b22, new_n), new_n);

	// Final result reconstruction
	vector<vector<int>> c(n, vector<int>(n));
	auto c11 = add(sub(add(p1, p4, new_n), p5, new_n), p7, new_n);
	auto c12 = add(p3, p5, new_n);
	auto c21 = add(p2, p4, new_n);
	auto c22 = add(sub(add(p1, p3, new_n), p2, new_n), p6, new_n);

	for (int i = 0; i < new_n; i++) {
		for (int j = 0; j < new_n; j++) {
			c[i][j] = c11[i][j];
			c[i][j + new_n] = c12[i][j];
			c[i + new_n][j] = c21[i][j];
			c[i + new_n][j + new_n] = c22[i][j];
		}
	}
	return c;
}

int main() {
	// Note: This recovery version assumes 2^n matrices as per the report's logic
	int n = 4;
	vector<vector<int>> A = { {1, 2, 3, 4}, {5, 6, 7, 8}, {9, 1, 2, 3}, {4, 5, 6, 7} };
	vector<vector<int>> B = { {8, 7, 6, 5}, {4, 3, 2, 1}, {5, 6, 7, 8}, {1, 2, 3, 4} };

	auto result = strassen(A, B, n);

	cout << "Resultant Matrix C:" << endl; 
	for (auto row : result) {
		for (int val : row) cout << val << " ";
		cout << endl;
	}
	return 0;
}
