CREATE TABLE [eventdata] (
	[EventdataTime]         TEXT,
	[EventdataDevId]        INTEGER,
	[EventdataDevInfo]      TEXT,
	[EventdataPriority]     INTEGER,
	[EventdataDescription]  TEXT
);

INSERT INTO [eventdata] values (
	datetime(),
	0,
	'DATABASE',
	0,
	'Database created.'
);
