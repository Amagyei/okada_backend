                        ```mermaid
                        graph TB
                            subgraph Actors
                                Rider((Rider))
                                Driver((Driver))
                                Admin((Admin))
                                PaymentGateway((Payment Gateway))
                            end

                            subgraph "Phase 1: Current State [P]"
                                subgraph "Authentication [x]"
                                    Register[Register Account]
                                    Login[Login]
                                    VerifyPhone[Verify Phone]
                                    VerifyEmail[Verify Email]
                                    UpdateProfile[Update Profile]
                                end

                                subgraph "User Management [x]"
                                    ViewProfile[View Profile]
                                    EditProfile[Edit Profile]
                                    UploadDocuments[Upload Documents]
                                end

                                subgraph "Location Management [x]"
                                    SaveLocation[Save Location]
                                    ViewSavedLocations[View Saved Locations]
                                    SetDefaultLocation[Set Default Location]
                                end

                                subgraph "Ride Management [P]"
                                    RequestRide[Request Ride]
                                    AcceptRide[Accept Ride]
                                    TrackRide[Track Ride]
                                    CompleteRide[Complete Ride]
                                    CancelRide[Cancel Ride]
                                    RateRide[Rate Ride]
                                end

                                subgraph "Payment Management [!]"
                                    AddPaymentMethod[Add Payment Method]
                                    ProcessPayment[Process Payment]
                                    ViewTransactions[View Transactions]
                                    WithdrawEarnings[Withdraw Earnings]
                                end
                            end

                            subgraph "Phase 2: Target State"
                                subgraph "Map Integration [!]"
                                    ViewMap[View Map]
                                    SearchLocation[Search Location]
                                    SelectPickup[Select Pickup]
                                    SelectDestination[Select Destination]
                                    ViewRoute[View Route]
                                end

                                subgraph "Real-time Updates [!]"
                                    UpdateLocation[Update Location]
                                    TrackDriver[Track Driver]
                                    ReceiveNotifications[Receive Notifications]
                                end

                                subgraph "Advanced Ride Features [!]"
                                    EstimateFare[Estimate Fare]
                                    MatchDriver[Match Driver]
                                    CalculateFinalFare[Calculate Final Fare]
                                    ViewRideHistory[View Ride History]
                                end

                                subgraph "Payment Processing [!]"
                                    MobileMoneyPayment[Mobile Money Payment]
                                    ProcessRidePayment[Process Ride Payment]
                                    HandleRefunds[Handle Refunds]
                                end
                            end

                            %% Current Phase Relationships
                            Rider --> Register
                            Rider --> Login
                            Rider --> VerifyPhone
                            Rider --> UpdateProfile
                            Rider --> ViewProfile
                            Rider --> EditProfile
                            Rider --> SaveLocation
                            Rider --> ViewSavedLocations
                            Rider --> RequestRide
                            Rider --> TrackRide
                            Rider --> CancelRide
                            Rider --> RateRide

                            Driver --> Register
                            Driver --> Login
                            Driver --> VerifyPhone
                            Driver --> UpdateProfile
                            Driver --> UploadDocuments
                            Driver --> AcceptRide
                            Driver --> CompleteRide
                            Driver --> CancelRide

                            %% Target Phase Relationships
                            Rider -.-> ViewMap
                            Rider -.-> SearchLocation
                            Rider -.-> SelectPickup
                            Rider -.-> SelectDestination
                            Rider -.-> ViewRoute
                            Rider -.-> TrackDriver
                            Rider -.-> ReceiveNotifications
                            Rider -.-> EstimateFare
                            Rider -.-> ViewRideHistory
                            Rider -.-> MobileMoneyPayment

                            Driver -.-> UpdateLocation
                            Driver -.-> ReceiveNotifications
                            Driver -.-> MatchDriver
                            Driver -.-> CalculateFinalFare
                            Driver -.-> ProcessRidePayment

                            %% System Relationships
                            RequestRide --> EstimateFare
                            AcceptRide --> MatchDriver
                            CompleteRide --> CalculateFinalFare
                            CalculateFinalFare --> ProcessRidePayment
                            ProcessRidePayment --> MobileMoneyPayment

                            %% Styling
                            style Rider fill:#f9f,stroke:#333,stroke-width:2px
                            style Driver fill:#bbf,stroke:#333,stroke-width:2px
                            style Admin fill:#bfb,stroke:#333,stroke-width:2px
                            style PaymentGateway fill:#fbb,stroke:#333,stroke-width:2px

                            %% Legend
                            subgraph Legend
                                Completed[x]
                                InProgress[P]
                                Blocked[!]
                                Pending[-]
                            end
                        ``` 