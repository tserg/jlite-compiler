class Main {
	 Void main(){
	 	Int i;
		Int j;
		Bool k;
		SimpleMain sm;

		sm = new SimpleMain();

		i = 7;
		j = 0;
		k = true;
		println(i);
		println("\n");
		if (k) {

			if (i < j) {
				i = 5;
			} else {
				j = 3;
				i = sm.getSum(i, j);
			}
		} else {
			println("Nothing happens!\n");
		}

		println(i);
		println("\n");
		println(j);
	 }

 }

class SimpleMain {
	Bool c;

	String getString(String x){
		return x;
	}

	Int getSum(Int a, Int b) {

		return a+b;
	}
}
