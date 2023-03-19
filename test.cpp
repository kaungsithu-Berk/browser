#include <iostream>

#include <iomanip>

using namespace std;




int main()

{

    //Declare variables

    int numCups = 0;

    int consumedCaffeine;

    double retainedCaffeine;

    

    cout << "Enter number of cups: ";

    cin >> numCups;

    consumedCaffeine = numCups * 130; // 130 mg in one cup

    cout << "Caffeine consumed (mg): " << consumedCaffeine << endl << endl;

    

    cout << setw(2) << "After Hour" << setw(15) << "mg caffeine" << endl;

    

    for (int hour = 1; hour <= 24; hour++) {

        retainedCaffeine = consumedCaffeine;

        for (int i = 1; i <= hour; i++) {

            retainedCaffeine = retainedCaffeine * 0.87;

        }

        cout << setw(3) << hour << setw(18) << fixed << setprecision(1) << retainedCaffeine << endl;

    }

    return 0;

}