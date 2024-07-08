document.addEventListener('DOMContentLoaded', function () {
    var trackDriverBtn = document.getElementById('track-driver-btn');
    var driverInfoSection = document.getElementById('driver-info');
    var driverList = document.querySelector('.driver-list'); // Corrected selector for driver list

    var drivers = ['Driver Name 1', 'Driver Name 2', 'Driver Name 3'];

    trackDriverBtn.addEventListener('click', function () {
        driverInfoSection.classList.toggle('hidden');

        if (!driverInfoSection.classList.contains('hidden')) {
            driverList.innerHTML = '';

            drivers.forEach(function (driver) {
                var driverElement = document.createElement('div');
                driverElement.classList.add('driver');

                var driverName = document.createElement('h3');
                driverName.classList.add('driver-name');
                driverName.textContent = driver;

                var trackBtn = document.createElement('button');
                trackBtn.classList.add('track-btn');
                trackBtn.textContent = 'Track';

                driverElement.appendChild(driverName);
                driverElement.appendChild(trackBtn);
                driverList.appendChild(driverElement);
            });
        }
    });
});
