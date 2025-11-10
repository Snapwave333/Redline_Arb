using System;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace CalmCadence.Data.Context;

public class CalmCadenceDbContextFactory : IDesignTimeDbContextFactory<CalmCadenceDbContext>
{
    public CalmCadenceDbContext CreateDbContext(string[] args)
    {
        var builder = new DbContextOptionsBuilder<CalmCadenceDbContext>();

        // Local SQLite database file in solution root
        var connectionString = "Data Source=calmcadence.db";
        builder.UseSqlite(connectionString);

        return new CalmCadenceDbContext(builder.Options);
    }
}
